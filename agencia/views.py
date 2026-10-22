"""Área da agência parceira.

O painel tem a visão geral, a lista de orçamentos e os dados da agência. O
orçamento é feito direto no card da página da viagem (`orcamento_criar`), sem
abrir o painel, sai em PDF para o e-mail que a agência digitar no pop-up e
fica na aba Orçamentos para acompanhar (aceito, recusado, vencido).

Uma agência (um CNPJ) pode ter vários agentes, cada um com o seu login. A aba
Orçamentos mostra os de todos os agentes da agência, com o nome de quem fez;
só quem fez muda a situação do orçamento.

Toda consulta daqui passa por `request.agencia`. É isso que impede uma agência
de ver cliente de outra.
"""
import logging
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

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


def _orcamentos_da_agencia(agencia):
    """Orçamentos de todos os agentes com o mesmo CNPJ."""
    return (Orcamento.objects.filter(agencia__cnpj=agencia.cnpj)
            .select_related('destino', 'agencia__usuario'))


@agencia_aprovada
def painel(request):
    orcamentos = _orcamentos_da_agencia(request.agencia)
    return render(request, 'agencia/painel.html', {
        'aba': 'painel',
        'interessados': request.agencia.interessados.select_related('destino'),
        'ultimos_orcamentos': orcamentos[:5],
        'total_orcamentos': orcamentos.count(),
    })


FILTROS_ORCAMENTO = [
    ('', 'Todos'),
    ('enviado', 'Aguardando o cliente'),
    ('aceito', 'Aceitos'),
    ('recusado', 'Recusados'),
    ('vencido', 'Vencidos'),
]


@agencia_aprovada
def orcamentos(request):
    """Todos os orçamentos da agência, para acompanhar."""
    todos = _orcamentos_da_agencia(request.agencia)
    filtro = request.GET.get('situacao', '')
    agora = timezone.now()
    lista = todos
    if filtro == 'vencido':
        lista = todos.filter(status='enviado', valido_ate__lt=agora)
    elif filtro == 'enviado':
        lista = todos.filter(status='enviado').exclude(valido_ate__lt=agora)
    elif filtro in ('aceito', 'recusado'):
        lista = todos.filter(status=filtro)
    else:
        filtro = ''
    aceitos = todos.filter(status='aceito')
    return render(request, 'agencia/orcamentos.html', {
        'aba': 'orcamentos',
        'orcamentos': lista[:200],
        'filtro': filtro,
        'filtros': FILTROS_ORCAMENTO,
        'resumo': {
            'total': todos.count(),
            'aguardando': todos.filter(status='enviado').exclude(valido_ate__lt=agora).count(),
            'aceitos': aceitos.count(),
            'valor_aceito': sum((o.valor or Decimal('0')) for o in aceitos),
        },
        'varios_agentes': todos.values('agencia').distinct().count() > 1,
    })


@require_POST
@agencia_aprovada
def orcamento_situacao(request, pk):
    """O agente que fez o orçamento marca se o cliente aceitou ou recusou."""
    orcamento = get_object_or_404(Orcamento, pk=pk, agencia=request.agencia)
    nova = request.POST.get('situacao')
    if nova in dict(Orcamento.STATUS):
        orcamento.status = nova
        orcamento.save(update_fields=['status', 'atualizado_em'])
        messages.success(request, 'Orçamento {} marcado como "{}".'.format(
            orcamento.codigo, orcamento.get_status_display().lower()))
    voltar = request.POST.get('voltar', '')
    if voltar not in dict(FILTROS_ORCAMENTO):
        voltar = ''
    return redirect('{}?situacao={}'.format(reverse('agencia:orcamentos'), voltar))


@agencia_aprovada
def minha_agencia(request):
    return render(request, 'agencia/minha_agencia.html', {
        'aba': 'agencia',
    })


@require_POST
@agencia_aprovada
def orcamento_criar(request, slug):
    """Recebe o orçamento do card da viagem e volta para a mesma página.

    O valor sai da tabela da viagem: para cada tipo de quarto escolhido, o preço
    por pessoa dele vezes as pessoas nele. Criança é sob consulta e fica fora da conta.
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
    # tipo sem preço na tabela: o orçamento todo fica "sob consulta"
    if all(q['preco'] is not None for q in orcamento.quartos):
        orcamento.valor = sum(Decimal(q['preco']) * q['pessoas'] for q in orcamento.quartos)
    else:
        orcamento.valor = None
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
    # qualquer agente da mesma agência (mesmo CNPJ) baixa o PDF
    orcamento = get_object_or_404(Orcamento.objects.select_related('destino', 'agencia__usuario'),
                                  pk=pk, agencia__cnpj=request.agencia.cnpj)
    resposta = HttpResponse(gerar_pdf(orcamento), content_type='application/pdf')
    resposta['Content-Disposition'] = 'inline; filename="{}"'.format(_nome_do_pdf(orcamento))
    return resposta
