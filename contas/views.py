"""Entrar, cadastrar e sair.

Quem é dono do site não passa por aqui para administrar: o painel do dono é o
admin do Django, em /painel/. Estas telas são a porta do cliente.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CadastroForm, EntrarForm


def _proxima_pagina(request):
    """Para onde mandar a pessoa depois de entrar.

    Só aceita destino dentro do próprio site: um `?next=` apontando para fora
    seria um convite a golpe de redirecionamento.
    """
    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return reverse('destinations:home')


def entrar(request):
    if request.user.is_authenticated:
        return redirect(_proxima_pagina(request))

    if request.method == 'POST':
        form = EntrarForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Bem-vindo(a) de volta, {}!'.format(
                request.user.first_name or request.user.username))
            return redirect(_proxima_pagina(request))
    else:
        form = EntrarForm(request)

    return render(request, 'contas/entrar.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def cadastro(request):
    if request.user.is_authenticated:
        return redirect(_proxima_pagina(request))

    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, 'Conta criada! Agora é só escolher a viagem.')
            return redirect(_proxima_pagina(request))
    else:
        form = CadastroForm()

    return render(request, 'contas/cadastro.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def sair(request):
    """Sai da conta.

    Só por POST: um `<a href="/sair/">` seria disparado por qualquer imagem ou
    link de terceiro e derrubaria a sessão da pessoa sem ela pedir.
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Você saiu da sua conta.')
    return redirect('destinations:home')


@login_required
def minha_conta(request):
    """Painel do cliente: dados da conta e as reservas que ele pediu."""
    return render(request, 'contas/conta.html', {
        'reservas': request.user.reservas.select_related('destino'),
    })
