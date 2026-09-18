"""Entrar com Google (OAuth 2.0 / OpenID Connect).

Como funciona, em três passos:

1. A pessoa clica em "Continuar com Google". O site guarda um `state` na
   sessão e manda a pessoa para a tela de consentimento do Google.
2. O Google devolve a pessoa para /entrar/google/retorno/ com um `code`.
3. O site troca o `code` por um token, pede ao Google o e-mail e o nome da
   pessoa, e entra (ou cria) a conta com aquele e-mail.

Não há senha envolvida: o Google já confirmou que o e-mail é da pessoa, então
a conta nasce ativa. Quem já tinha conta com o mesmo e-mail entra nela — e, se
ainda não tinha confirmado o e-mail, a confirmação fica feita aqui.

Configuração (ver .env.example): SOAR_GOOGLE_CLIENT_ID e SOAR_GOOGLE_CLIENT_SECRET.
Sem elas, o botão nem aparece.

Só usa a biblioteca padrão do Python — nada novo para instalar.
"""
import json
import logging
import re
import secrets
from urllib import error, parse, request as http

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

log = logging.getLogger('soar.seguranca')

URL_AUTORIZACAO = 'https://accounts.google.com/o/oauth2/v2/auth'
URL_TOKEN = 'https://oauth2.googleapis.com/token'
URL_PERFIL = 'https://openidconnect.googleapis.com/v1/userinfo'
ESCOPOS = 'openid email profile'
CHAVE_SESSAO = 'google_oauth'


class ErroGoogle(Exception):
    """Alguma etapa do login com Google falhou. A mensagem é para a pessoa."""


def configurado():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def url_de_retorno(request):
    """Tem que ser idêntica à cadastrada no Google Cloud Console."""
    return request.build_absolute_uri(reverse('contas:google_retorno'))


def iniciar(request, proxima=''):
    """Monta a URL do Google e guarda o `state` na sessão.

    O `state` é o que impede alguém de colar um `code` alheio no retorno
    (CSRF no login): só vale o retorno que traz o mesmo valor sorteado aqui.
    """
    state = secrets.token_urlsafe(32)
    request.session[CHAVE_SESSAO] = {'state': state, 'next': proxima}
    parametros = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': url_de_retorno(request),
        'response_type': 'code',
        'scope': ESCOPOS,
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return URL_AUTORIZACAO + '?' + parse.urlencode(parametros)


def _post_json(url, dados=None, cabecalhos=None):
    corpo = parse.urlencode(dados).encode() if dados else None
    req = http.Request(url, data=corpo, headers=cabecalhos or {})
    if corpo is not None:
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with http.urlopen(req, timeout=15) as resposta:
            return json.loads(resposta.read().decode())
    except error.HTTPError as e:
        detalhe = e.read().decode(errors='replace')[:300]
        log.warning('google: %s respondeu %s: %s', url, e.code, detalhe)
        raise ErroGoogle('O Google não aceitou o login. Tente de novo.')
    except (error.URLError, TimeoutError, ValueError) as e:
        log.warning('google: falha ao falar com %s: %s', url, e)
        raise ErroGoogle('Não foi possível falar com o Google agora. Tente de novo em instantes.')


def concluir(request):
    """Valida o retorno do Google e devolve (usuario, proxima_pagina).

    Levanta ErroGoogle com uma mensagem própria para a tela em qualquer
    problema: state errado, pessoa cancelou, e-mail não verificado...
    """
    guardado = request.session.pop(CHAVE_SESSAO, None)
    proxima = (guardado or {}).get('next', '')

    if request.GET.get('error'):
        # A pessoa clicou em "cancelar" na tela do Google.
        raise ErroGoogle('Login com Google cancelado.')

    state = request.GET.get('state', '')
    codigo = request.GET.get('code', '')
    if not guardado or not state or not secrets.compare_digest(state, guardado['state']):
        raise ErroGoogle('O login com Google expirou ou veio de outra aba. Tente de novo.')
    if not codigo:
        raise ErroGoogle('O Google não devolveu o código de acesso. Tente de novo.')

    token = _post_json(URL_TOKEN, {
        'code': codigo,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': url_de_retorno(request),
        'grant_type': 'authorization_code',
    })
    acesso = token.get('access_token')
    if not acesso:
        raise ErroGoogle('O Google não liberou o acesso. Tente de novo.')

    perfil = _post_json(URL_PERFIL, cabecalhos={'Authorization': 'Bearer ' + acesso})
    email = (perfil.get('email') or '').strip().lower()
    if not email or not perfil.get('email_verified'):
        # Sem e-mail verificado não dá para saber de quem é a conta.
        raise ErroGoogle('Sua conta Google não tem um e-mail verificado. '
                         'Use o cadastro com e-mail e senha.')

    usuario, criado = _usuario_para(email, perfil.get('given_name') or perfil.get('name') or '')
    log.info('login google %s: usuario=%r email=%s', 'criou conta' if criado else 'ok',
             usuario.get_username(), email)
    return usuario, proxima, criado


def _usuario_para(email, nome):
    """Acha a conta pelo e-mail ou cria uma nova, já ativa."""
    usuario = User.objects.filter(email__iexact=email).first()
    if usuario:
        mudou = []
        if not usuario.is_active:
            # O Google confirmou o e-mail; é a mesma prova que o link daria.
            usuario.is_active = True
            mudou.append('is_active')
        if not usuario.first_name and nome:
            usuario.first_name = nome[:60]
            mudou.append('first_name')
        if mudou:
            usuario.save(update_fields=mudou)
        return usuario, False

    usuario = User(username=_username_livre(email), email=email,
                   first_name=nome[:60], is_active=True)
    # Sem senha: esta conta entra pelo Google. (O "esqueci minha senha" do
    # Django ignora contas sem senha, de propósito — a pessoa continua
    # entrando pelo Google, que foi o que ela escolheu.)
    usuario.set_unusable_password()
    usuario.save()
    return usuario, True


def _username_livre(email):
    """Deriva um nome de usuário do e-mail e garante que não existe outro igual."""
    base = re.sub(r'[^\w.@+-]', '', email.split('@', 1)[0])[:140] or 'viajante'
    candidato = base
    n = 1
    while User.objects.filter(username__iexact=candidato).exists():
        n += 1
        candidato = '{}{}'.format(base[:140 - len(str(n))], n)
    return candidato


def usuario_entra_pelo_google(usuario):
    """Conta criada pelo Google não tem senha — algumas telas mudam por isso."""
    return not usuario.has_usable_password()
