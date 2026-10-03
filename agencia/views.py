"""Área da agência parceira.

O painel ficou só com a visão geral e os dados da agência. O orçamento é feito
direto no card da página da viagem (`orcamento_criar`), sem abrir o painel, e
sai em PDF para o e-mail que a agência digitar no pop-up.

Toda consulta daqui passa por `request.agencia`. É isso que impede uma agência
de ver cliente de outra.
"""
import logging
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from destinations.conteudo import tabela_de_precos
from destinations.models import Destino
from soar.seguranca import LIMITE_ORCAMENTO

from .forms import OrcamentoViagemForm
from .models import AVISO, Orcamento
from .pdf import gerar_pdf

log = logging.getLogger('soar.seguranca')


def agencia_aprovada(view):
    """Só entra a agência que a Soar já aprovou."""
    @login_required
    @wraps(view)
    def envolta(request, *args, **kwargs):
        agencia = getattr(request.user, 'agente', None)
        if agencia is None:
            messages.info(request, 'Esta área é exclusiva das agências parceiras.')
            return redirect('contas:minha_conta')
        if not agencia.aprovado:
            return redirect('contas:agente_area')
        request.agencia = agencia
        return view(request, *args, **kwargs)
    return envolta


@agencia_aprovada
def painel(request):
    return render(request, 'agencia/painel.html', {
        'aba': 'painel',
        'interessados': request.agencia.interessados.select_related('destino'),
    })


@agencia_aprovada
def minha_agencia(request):
    return render(request, 'agencia/minha_agencia.html', {
        'aba': 'agencia',
    })


@require_POST
@agencia_aprovada
def orcamento_criar(request, slug):
    """Recebe o orçamento do card da viagem e volta para a mesma página.

    O valor sai da tabela da viagem: preço por adulto da acomodação escolhida
    vezes o número de adultos. Criança é sob consulta e fica fora da conta.
    """
    from destinations.views import pagina_da_viagem

    destino = get_object_or_404(Destino, slug=slug)
    form = OrcamentoViagemForm(request.POST, destino=destino)
    if form.is_valid() and LIMITE_ORCAMENTO.estourou(request, request.agencia.pk):
        log.warning('orcamento bloqueado por limite: agencia=%s', request.agencia.pk)
        form.add_error(None, 'Muitos orçamentos enviados na última hora. Espere um pouco e '
                             'tente de novo.')
    if not form.is_valid():
        return pagina_da_viagem(request, destino, form_orcamento=form)

    orcamento = form.save(commit=False)
    orcamento.agencia = request.agencia
    orcamento.destino = destino
    preco = tabela_de_precos(destino).get(orcamento.acomodacao)
    orcamento.valor = preco * orcamento.pessoas if preco is not None else None
    orcamento.save()
    LIMITE_ORCAMENTO.registrar(request, request.agencia.pk)
    log.info('orcamento criado: agencia=%s orcamento=%s destino=%s',
             request.agencia.pk, orcamento.codigo, destino.slug)

    # O orçamento fica salvo mesmo se o e-mail falhar: a página avisa e oferece
    # o PDF para baixar e mandar por outro caminho.
    try:
        _enviar_por_email(orcamento)
    except Exception:
        log.exception('orcamento sem e-mail: orcamento=%s', orcamento.codigo)
    else:
        orcamento.enviado_em = timezone.now()
        orcamento.save(update_fields=['enviado_em'])
    return redirect('{}?orcamento={}#reservar'.format(destino.get_absolute_url(), orcamento.pk))


def _enviar_por_email(orcamento):
    """Manda o PDF para o e-mail do responsável; a resposta cai na agência."""
    agencia = orcamento.agencia
    corpo = render_to_string('agencia/email/orcamento.txt', {
        'orcamento': orcamento, 'agencia': agencia, 'aviso': AVISO,
        'valido_ate': timezone.localtime(orcamento.valido_ate),
    })
    mensagem = EmailMessage(
        'Orçamento {} - {} | {}'.format(orcamento.codigo, orcamento.destino.nome,
                                        agencia.razao_social),
        corpo, settings.DEFAULT_FROM_EMAIL, [orcamento.cliente_email],
        reply_to=[agencia.usuario.email] if agencia.usuario.email else None,
    )
    mensagem.attach(_nome_do_pdf(orcamento), gerar_pdf(orcamento), 'application/pdf')
    mensagem.send()


def _nome_do_pdf(orcamento):
    return 'orcamento-{}.pdf'.format(orcamento.codigo)


@agencia_aprovada
def orcamento_pdf(request, pk):
    """O mesmo PDF do e-mail, para a agência baixar. Só o orçamento dela."""
    orcamento = get_object_or_404(Orcamento.objects.select_related('destino', 'agencia__usuario'),
                                  pk=pk, agencia=request.agencia)
    resposta = HttpResponse(gerar_pdf(orcamento), content_type='application/pdf')
    resposta['Content-Disposition'] = 'inline; filename="{}"'.format(_nome_do_pdf(orcamento))
    return resposta
