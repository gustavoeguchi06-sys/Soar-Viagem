"""Pedido de reserva — a parte do site que exige conta.

O `@login_required` é o que garante a regra: sem estar logado, a pessoa é
mandada para a tela de entrar e volta para cá assim que entrar.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from destinations.conteudo import montar_viagem
from destinations.models import Destino
from soar.seguranca import LIMITE_RESERVA

from .forms import ReservaForm
from .models import Reserva


@login_required
def nova(request, slug):
    destino = get_object_or_404(Destino, slug=slug)
    viagem = montar_viagem(destino, list(destino.avaliacoes.all()))
    saidas = viagem['saidas']

    # Todas as datas cadastradas estão lotadas: não tem o que pedir aqui.
    if saidas and not viagem['tem_vaga']:
        messages.info(request, 'Todas as saídas desta viagem estão esgotadas. '
                               'Fale com a Soar pelo WhatsApp para entrar na lista de espera.')
        return redirect(destino.get_absolute_url())

    if request.method == 'POST':
        # Uma conta so nao enche a fila do painel de pedido falso.
        if LIMITE_RESERVA.estourou(request, request.user.pk):
            messages.error(request, 'Você enviou muitos pedidos agora há pouco. '
                                    'Fale com a Soar pelo WhatsApp se precisar de mais.')
            return redirect('contas:minha_conta')

        # Pedido repetido para o mesmo destino, com um ainda aguardando
        # contato, e so retrabalho para a equipe.
        ja_pendente = Reserva.objects.filter(
            usuario=request.user, destino=destino, status='pendente').exists()
        if ja_pendente:
            messages.info(request, 'Você já tem um pedido aguardando contato para este '
                                   'destino. Nosso time vai falar com você.')
            return redirect('contas:minha_conta')

        form = ReservaForm(request.POST, saidas=saidas)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.destino = destino
            # o preço do dia do pedido fica gravado: se a tabela mudar depois,
            # vale o que foi combinado com o cliente
            escolhida = next((a for a in viagem['acomodacoes']
                              if a['chave'] == reserva.acomodacao), None)
            reserva.preco_estimado = escolhida['valor'] if escolhida else None
            escolhida_id = form.cleaned_data.get('saida_escolhida')
            saida = next((s for s in saidas if str(s['id']) == escolhida_id), None)
            reserva.saida = saida['texto'] if saida else viagem['proxima_saida']
            reserva.save()
            LIMITE_RESERVA.registrar(request, request.user.pk)
            messages.success(
                request,
                'Reserva {} enviada! Nosso time entra em contato para confirmar.'.format(
                    reserva.codigo)
            )
            return redirect('contas:minha_conta')
    else:
        escolha = request.GET.get('acomodacao', 'casal')
        chaves = [a['chave'] for a in viagem['acomodacoes']]
        livres = [str(s['id']) for s in saidas if not s['esgotada']]
        data = request.GET.get('saida', '')
        form = ReservaForm(saidas=saidas, initial={
            'acomodacao': escolha if escolha in chaves else 'casal',
            'pessoas': 2 if escolha in ('casal', 'duplo', '') else 1,
            'saida_escolhida': data if data in livres else (livres[0] if livres else None),
        })

    return render(request, 'reservas/nova.html', {
        'destino': destino,
        'viagem': viagem,
        'form': form,
    })


@login_required
def cancelar(request, pk):
    """O cliente desiste de um pedido que ainda não foi confirmado."""
    reserva = get_object_or_404(Reserva, pk=pk, usuario=request.user)
    if request.method == 'POST':
        if reserva.status == 'pendente':
            reserva.status = 'cancelada'
            reserva.save(update_fields=['status', 'atualizado_em'])
            messages.success(request, 'Reserva {} cancelada.'.format(reserva.codigo))
        else:
            messages.error(
                request,
                'A reserva {} já foi {}. Fale com a Soar para alterar.'.format(
                    reserva.codigo, reserva.get_status_display().lower())
            )
    return redirect('contas:minha_conta')
