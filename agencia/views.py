"""Painel da agência parceira.

Uma tela de trabalho só da agência, separada do painel do dono: ela vê as
reservas dos clientes que chegaram pelo link dela e os orçamentos que montou.

Toda consulta daqui passa por `request.agencia`. É isso que impede uma agência
de ver cliente de outra: o `get_object_or_404(..., agencia=request.agencia)`
devolve 404 para qualquer reserva ou orçamento que não seja dela, mesmo que
alguém troque o número na barra de endereço.
"""
import logging
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from reservas.models import Reserva

from .forms import AtendimentoForm, OrcamentoForm
from .models import Orcamento

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


def _filtro_status(request, escolhas):
    status = request.GET.get('status', '')
    return status if status in dict(escolhas) else ''


@agencia_aprovada
def painel(request):
    agencia = request.agencia
    reservas = Reserva.objects.filter(agencia=agencia)
    orcamentos = Orcamento.objects.filter(agencia=agencia)

    r = reservas.aggregate(
        pendentes=Count('pk', filter=Q(status='pendente')),
        confirmadas=Count('pk', filter=Q(status='confirmada')),
    )
    o = orcamentos.aggregate(
        abertos=Count('pk', filter=Q(status='enviado')),
        aceitos=Count('pk', filter=Q(status='aceito')),
        vendido=Sum('valor', filter=Q(status='aceito')),
    )

    return render(request, 'agencia/painel.html', {
        'aba': 'painel',
        'numeros': {**r, **o},
        'pendentes': reservas.filter(status='pendente')
                             .select_related('destino', 'usuario')[:5],
        'orcamentos_abertos': orcamentos.filter(status='enviado')
                                        .select_related('destino')[:5],
        'link_indicacao': request.build_absolute_uri(
            reverse('destinations:home') + '?ag=' + agencia.codigo),
    })


@agencia_aprovada
def reservas(request):
    status = _filtro_status(request, Reserva.STATUS)
    lista = (Reserva.objects.filter(agencia=request.agencia)
             .select_related('destino', 'usuario'))
    contagem = dict(lista.values_list('status').annotate(n=Count('pk')))
    if status:
        lista = lista.filter(status=status)
    return render(request, 'agencia/reservas.html', {
        'aba': 'reservas',
        'reservas': lista,
        'status': status,
        'filtros': [(chave, nome, contagem.get(chave, 0)) for chave, nome in Reserva.STATUS],
        'total': sum(contagem.values()),
    })


@agencia_aprovada
def reserva(request, pk):
    reserva = get_object_or_404(Reserva.objects.select_related('destino', 'usuario'),
                                pk=pk, agencia=request.agencia)
    form = AtendimentoForm(request.POST or None, instance=reserva)
    if request.method == 'POST' and form.is_valid():
        mudou_status = 'status' in form.changed_data
        form.save()
        if mudou_status:
            log.info('agencia mudou reserva: agencia=%s reserva=%s status=%s',
                     request.agencia.pk, reserva.codigo, reserva.status)
        messages.success(request, 'Reserva {} atualizada.'.format(reserva.codigo))
        return redirect('agencia:reservas')
    return render(request, 'agencia/reserva.html', {
        'aba': 'reservas', 'reserva': reserva, 'form': form,
    })


@agencia_aprovada
def orcamentos(request):
    status = _filtro_status(request, Orcamento.STATUS)
    lista = Orcamento.objects.filter(agencia=request.agencia).select_related('destino')
    contagem = dict(lista.values_list('status').annotate(n=Count('pk')))
    if status:
        lista = lista.filter(status=status)
    return render(request, 'agencia/orcamentos.html', {
        'aba': 'orcamentos',
        'orcamentos': lista,
        'status': status,
        'filtros': [(chave, nome, contagem.get(chave, 0)) for chave, nome in Orcamento.STATUS],
        'total': sum(contagem.values()),
    })


@agencia_aprovada
def orcamento_novo(request):
    form = OrcamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        orcamento = form.save(commit=False)
        orcamento.agencia = request.agencia
        orcamento.save()
        messages.success(request, 'Orçamento {} criado.'.format(orcamento.codigo))
        return redirect('agencia:orcamentos')
    return render(request, 'agencia/orcamento_form.html', {
        'aba': 'orcamentos', 'form': form, 'orcamento': None,
    })


@agencia_aprovada
def orcamento_editar(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk, agencia=request.agencia)
    form = OrcamentoForm(request.POST or None, instance=orcamento)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Orçamento {} salvo.'.format(orcamento.codigo))
        return redirect('agencia:orcamentos')
    return render(request, 'agencia/orcamento_form.html', {
        'aba': 'orcamentos', 'form': form, 'orcamento': orcamento,
    })


@agencia_aprovada
def minha_agencia(request):
    return render(request, 'agencia/minha_agencia.html', {
        'aba': 'agencia',
        'link_indicacao': request.build_absolute_uri(
            reverse('destinations:home') + '?ag=' + request.agencia.codigo),
    })
