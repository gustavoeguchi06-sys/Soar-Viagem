"""Entrar, cadastrar, confirmar e-mail, sair e cuidar dos próprios dados.

Quem é dono do site não passa por aqui para administrar: o painel do dono é o
admin do Django, em /painel/. Estas telas são a porta do cliente.
"""
import json
import logging

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (url_has_allowed_host_and_scheme, urlsafe_base64_decode,
                               urlsafe_base64_encode)

from soar.seguranca import LIMITE_CADASTRO, LIMITE_LOGIN, ip_do_cliente

from . import google
from .forms import AgenteCadastroForm, CadastroForm, EntrarForm, ExcluirContaForm

log = logging.getLogger('soar.seguranca')


def _e_do_painel(destino):
    """O caminho pedido é uma tela do painel do dono?"""
    return destino.startswith(reverse('admin:index'))


def _proxima_pagina(request):
    """Para onde mandar a pessoa depois de entrar.

    Só aceita destino dentro do próprio site: um `?next=` apontando para fora
    seria um convite a golpe de redirecionamento.

    Duas regras a mais, porque o site tem uma porta de entrada só:

    - quem é da equipe e entrou sem pedir página nenhuma vai direto ao painel,
      que é o lugar onde ela trabalha;
    - um cliente nunca é mandado para o painel, mesmo que o `next` diga isso.
      Ele não tem acesso, o painel devolveria ele para esta mesma tela e os dois
      ficariam se empurrando em círculo.
    """
    equipe = request.user.is_authenticated and request.user.is_staff

    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        if equipe or not _e_do_painel(destino):
            return destino

    if equipe:
        return reverse('admin:index')
    # Agência aprovada vai direto para o painel dela, o lugar onde ela trabalha.
    agencia = getattr(request.user, 'agente', None) if request.user.is_authenticated else None
    if agencia is not None and agencia.aprovado:
        return reverse('agencia:painel')
    return reverse('destinations:home')


def entrar(request):
    if request.user.is_authenticated:
        return redirect(_proxima_pagina(request))

    form = EntrarForm(request)

    if request.method == 'POST':
        digitado = request.POST.get('username', '').strip()

        # Antes de conferir a senha: esta pessoa já errou demais?
        # Sem este limite, dava para tentar senha à vontade — e a conta do dono
        # do site é superusuário, então adivinhá-la é administrar o site.
        if LIMITE_LOGIN.estourou(request, digitado):
            log.warning('login bloqueado por limite: usuario=%r ip=%s',
                        digitado, ip_do_cliente(request))
            messages.error(
                request,
                'Muitas tentativas seguidas. Espere alguns minutos antes de tentar de novo, '
                'ou use "esqueci minha senha".'
            )
            return render(request, 'contas/entrar.html', {
                'form': EntrarForm(request), 'next': request.GET.get('next', ''),
                'bloqueado': True,
            })

        form = EntrarForm(request, data=request.POST)
        if form.is_valid():
            LIMITE_LOGIN.limpar(request, digitado)
            login(request, form.get_user())
            messages.success(request, 'Bem-vindo(a) de volta, {}!'.format(
                request.user.first_name or request.user.username))
            return redirect(_proxima_pagina(request))

        # Erro de senha conta para o limite. O sinal user_login_failed já
        # registrou a tentativa no log (contas/apps.py).
        LIMITE_LOGIN.registrar(request, digitado)

    return render(request, 'contas/entrar.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def cadastro(request):
    if request.user.is_authenticated:
        return redirect(_proxima_pagina(request))

    if request.method == 'POST':
        if LIMITE_CADASTRO.estourou(request):
            messages.error(request, 'Muitos cadastros a partir daqui agora há pouco. '
                                    'Tente de novo mais tarde.')
            return render(request, 'contas/cadastro.html',
                          {'form': CadastroForm(), 'next': request.GET.get('next', '')})

        form = CadastroForm(request.POST)
        if form.is_valid():
            LIMITE_CADASTRO.registrar(request)
            email = form.cleaned_data['email']

            existente = User.objects.filter(email__iexact=email).first()
            if existente:
                # O endereço já tem conta. Não dá para dizer isso na tela sem
                # transformar o cadastro num consultor de "quem é cliente da
                # Soar". Quem precisa saber é o dono do e-mail, e é para ele
                # que a informação vai.
                _avisar_conta_existente(request, existente)
            else:
                try:
                    with transaction.atomic():
                        usuario = form.save()
                except IntegrityError:
                    # Corrida com outro cadastro do mesmo e-mail; o índice
                    # único do banco pegou. A resposta na tela não muda.
                    pass
                else:
                    _enviar_confirmacao(request, usuario)
                    log.info('conta criada: usuario=%r ip=%s',
                             usuario.get_username(), ip_do_cliente(request))

            # Mesma resposta nos dois caminhos — é isso que impede a enumeração.
            return render(request, 'contas/verifique_email.html', {'email': email})
    else:
        form = CadastroForm()

    return render(request, 'contas/cadastro.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def _link_absoluto(request, caminho):
    return request.build_absolute_uri(caminho)


def _enviar_confirmacao(request, usuario):
    """Manda o link que ativa a conta.

    Sem esta etapa, qualquer pessoa cadastrava com o e-mail de outra e a Soar
    acabava mandando confirmação de reserva para o endereço errado.
    """
    caminho = reverse('contas:ativar', kwargs={
        'uidb64': urlsafe_base64_encode(force_bytes(usuario.pk)),
        'token': default_token_generator.make_token(usuario),
    })
    corpo = render_to_string('contas/email/confirmar.txt', {
        'usuario': usuario,
        'link': _link_absoluto(request, caminho),
    })
    send_mail('Confirme seu e-mail | Soar Operadora', corpo, None, [usuario.email])


def _avisar_conta_existente(request, usuario):
    """Avisa o dono do endereço que alguém tentou cadastrar com o e-mail dele."""
    corpo = render_to_string('contas/email/ja_tem_conta.txt', {
        'usuario': usuario,
        'link_entrar': _link_absoluto(request, reverse('contas:entrar')),
        'link_senha': _link_absoluto(request, reverse('contas:senha_reset')),
    })
    send_mail('Você já tem conta na Soar', corpo, None, [usuario.email])


def ativar(request, uidb64, token):
    """Confirma o e-mail e liga a conta — sem entrar nela.

    O link só prova que alguém abriu aquele e-mail, não que é o dono da senha.
    Link de e-mail é reencaminhado, fica no histórico e é aberto sozinho pelos
    filtros antivírus de e-mail corporativo; se ele também fizesse login, quem
    clicasse primeiro ficaria com a sessão. Então ele só liga a conta, e a
    pessoa entra com a senha que acabou de criar.
    """
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        usuario = None

    if usuario is None or not default_token_generator.check_token(usuario, token):
        return render(request, 'contas/ativacao_invalida.html', status=400)

    if not usuario.is_active:
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])
        log.info('e-mail confirmado: usuario=%r ip=%s',
                 usuario.get_username(), ip_do_cliente(request))

    messages.success(request, 'E-mail confirmado! Agora é só entrar com seu usuário e senha.')
    return redirect('contas:entrar')


# --------------------------------------------------------------------------- #
# Entrar com Google
# --------------------------------------------------------------------------- #
def google_iniciar(request):
    """Manda a pessoa para a tela de consentimento do Google."""
    if not google.configurado():
        messages.error(request, 'Login com Google não está configurado neste site.')
        return redirect('contas:entrar')
    if request.user.is_authenticated:
        return redirect(_proxima_pagina(request))
    return redirect(google.iniciar(request, request.GET.get('next', '')))


def google_retorno(request):
    """O Google devolve a pessoa aqui, com o código de acesso."""
    if not google.configurado():
        return redirect('contas:entrar')
    try:
        usuario, proxima, criado = google.concluir(request)
    except google.ErroGoogle as e:
        messages.error(request, str(e))
        return redirect('contas:entrar')

    login(request, usuario)
    if criado:
        messages.success(request, 'Conta criada com o Google. Bem-vindo(a), {}!'.format(
            usuario.first_name or usuario.username))
    else:
        messages.success(request, 'Bem-vindo(a) de volta, {}!'.format(
            usuario.first_name or usuario.username))

    # Reaproveita a regra do `?next=` (só destino dentro do site, painel só
    # para a equipe) passando o destino guardado na sessão.
    request.GET = request.GET.copy()
    request.GET['next'] = proxima
    return redirect(_proxima_pagina(request))


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


def privacidade(request):
    """Aviso de privacidade — quais dados a Soar guarda e por quê (LGPD)."""
    return render(request, 'contas/privacidade.html')


@login_required
def meus_dados(request):
    """Baixa tudo o que a Soar guarda sobre a pessoa (LGPD, art. 18, II).

    JSON em vez de tela porque o direito é de *portabilidade*: o arquivo tem
    que servir para levar a outro lugar.
    """
    usuario = request.user
    dados = {
        'conta': {
            'usuario': usuario.username,
            'nome': usuario.get_full_name(),
            'email': usuario.email,
            'criada_em': usuario.date_joined.isoformat(),
            'ultimo_acesso': usuario.last_login.isoformat() if usuario.last_login else None,
        },
        'reservas': [
            {
                'codigo': r.codigo,
                'destino': r.destino.nome,
                'acomodacao': r.get_acomodacao_display(),
                'pessoas': r.pessoas,
                'telefone': r.telefone,
                'observacao': r.observacao,
                'preco_estimado': str(r.preco_estimado) if r.preco_estimado else None,
                'saida': r.saida,
                'agencia_parceira': r.agencia.razao_social if r.agencia else None,
                'situacao': r.get_status_display(),
                'pedido_em': r.criado_em.isoformat(),
            }
            for r in usuario.reservas.select_related('destino')
        ],
        'avaliacoes': [
            {
                'destino': a.destino.nome,
                'nota': a.nota,
                'comentario': a.comentario,
                'publicada': a.publicada,
                'criado_em': a.criado_em.isoformat(),
            }
            for a in usuario.avaliacoes.select_related('destino')
        ],
    }
    resposta = HttpResponse(
        json.dumps(dados, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8',
    )
    resposta['Content-Disposition'] = 'attachment; filename="meus-dados-soar.json"'
    log.info('exportacao de dados: usuario=%r ip=%s',
             usuario.get_username(), ip_do_cliente(request))
    return resposta


@login_required
def excluir_conta(request):
    """Apaga a conta e os dados pessoais (LGPD, art. 18, VI)."""
    if request.method == 'POST':
        form = ExcluirContaForm(request.user, request.POST)
        if form.is_valid():
            usuario = request.user
            nome = usuario.get_username()

            # As reservas ficam, porque a operadora precisa do histórico
            # comercial e fiscal — mas sem nada que ligue a pessoa a elas: o
            # telefone e as observações saem aqui, e o vínculo com a conta vira
            # NULL quando ela é apagada (Reserva.usuario é SET_NULL).
            usuario.reservas.update(telefone='', nota_agencia='',
                                    observacao='[dados removidos a pedido do cliente]')
            usuario.avaliacoes.update(nome_autor='Cliente removido', publicada=False)

            logout(request)
            usuario.delete()
            log.info('conta excluida a pedido: usuario=%r ip=%s', nome, ip_do_cliente(request))
            messages.success(request, 'Sua conta e seus dados pessoais foram apagados.')
            return redirect('destinations:home')
    else:
        form = ExcluirContaForm(request.user)

    return render(request, 'contas/excluir.html', {'form': form})


# --------------------------------------------------------------------------- #
# B2B — agentes de viagem
# --------------------------------------------------------------------------- #
def b2b(request):
    """Porta de entrada das agências: entrar ou ir para o cadastro B2B."""
    if request.user.is_authenticated:
        if hasattr(request.user, 'agente'):
            return redirect('contas:agente_area')
        return redirect(_proxima_pagina(request))

    form = EntrarForm(request)

    if request.method == 'POST':
        digitado = request.POST.get('username', '').strip()
        if LIMITE_LOGIN.estourou(request, digitado):
            log.warning('login b2b bloqueado por limite: usuario=%r ip=%s',
                        digitado, ip_do_cliente(request))
            messages.error(request, 'Muitas tentativas seguidas. Espere alguns minutos antes '
                                    'de tentar de novo, ou use "esqueci minha senha".')
            return render(request, 'contas/b2b.html',
                          {'form': EntrarForm(request), 'bloqueado': True})

        form = EntrarForm(request, data=request.POST)
        if form.is_valid():
            LIMITE_LOGIN.limpar(request, digitado)
            login(request, form.get_user())
            usuario = request.user
            messages.success(request, 'Bem-vindo(a), {}!'.format(
                usuario.first_name or usuario.username))
            if hasattr(usuario, 'agente'):
                return redirect('contas:agente_area')
            return redirect(_proxima_pagina(request))

        LIMITE_LOGIN.registrar(request, digitado)

    return render(request, 'contas/b2b.html', {'form': form})


def cadastro_agente(request):
    """Cadastro de agência de viagem (B2B), com confirmação por e-mail."""
    if request.user.is_authenticated:
        return redirect('contas:b2b')

    if request.method == 'POST':
        if LIMITE_CADASTRO.estourou(request):
            messages.error(request, 'Muitos cadastros a partir daqui agora há pouco. '
                                    'Tente de novo mais tarde.')
            return render(request, 'contas/b2b_cadastro.html', {'form': AgenteCadastroForm()})

        form = AgenteCadastroForm(request.POST)
        if form.is_valid():
            LIMITE_CADASTRO.registrar(request)
            email = form.cleaned_data['email']

            existente = User.objects.filter(email__iexact=email).first()
            if existente:
                # Mesmo cuidado do cadastro do cliente: não confirmar na tela se
                # o e-mail já tem conta. Quem precisa saber é o dono do endereço.
                _avisar_conta_existente(request, existente)
            else:
                try:
                    with transaction.atomic():
                        usuario = form.save()
                except IntegrityError:
                    pass
                else:
                    _enviar_confirmacao(request, usuario)
                    log.info('agencia cadastrada: usuario=%r ip=%s',
                             usuario.get_username(), ip_do_cliente(request))

            return render(request, 'contas/verifique_email.html', {'email': email})
    else:
        form = AgenteCadastroForm()

    return render(request, 'contas/b2b_cadastro.html', {'form': form})


@login_required
def agente_area(request):
    """Porta da agência parceira.

    Aprovada, a agência vai para o painel dela (app `agencia`). Enquanto a Soar
    confere o cadastro, fica nesta tela de espera com os dados enviados.
    """
    agente = getattr(request.user, 'agente', None)
    if agente is None:
        messages.info(request, 'Esta área é exclusiva das agências parceiras.')
        return redirect('contas:minha_conta')
    if agente.aprovado:
        return redirect('agencia:painel')
    return render(request, 'contas/agente_area.html', {'agente': agente})
