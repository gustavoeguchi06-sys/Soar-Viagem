"""Pedido de reserva — a parte do site que exige conta.

O `@login_required` é o que garante a regra: sem estar logado, a pessoa é
mandada para a tela de entrar e volta para cá assim que entrar.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from destinations.conteudo import montar_viagem
from destinations.models import Destino

from .forms import ReservaForm
from .models import Reserva


@login_required
def nova(request, slug):
    destino = get_object_or_404(Destino, slug=slug)
    viagem = montar_viagem(destino, list(destino.avaliacoes.all()))

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.destino = destino
            # o preço do dia do pedido fica gravado: se a tabela mudar depois,
            # vale o que foi combinado com o cliente
            escolhida = next((a for a in viagem['acomodacoes']
                              if a['chave'] == reserva.acomodacao), None)
            reserva.preco_estimado = escolhida['valor'] if escolhida else None
            reserva.saida = viagem['proxima_saida']
            reserva.save()
            messages.success(
                request,
                'Reserva {} enviada! Nosso time entra em contato para confirmar.'.format(
                    reserva.codigo)
            )
            return redirect('contas:minha_conta')
    else:
        escolha = request.GET.get('acomodacao', 'duplo')
        chaves = [a['chave'] for a in viagem['acomodacoes']]
        form = ReservaForm(initial={
            'acomodacao': escolha if escolha in chaves else 'duplo',
            'pessoas': 2 if escolha in ('duplo', '') else 1,
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
