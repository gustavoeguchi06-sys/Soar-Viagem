"""Verificação em duas etapas da equipe (senha + código do celular).

A porta que importa é o painel do dono: quem entra lá é superusuário. Então a
exigência fica no próprio painel (`soar.painel.PainelSoar.has_permission`),
e não em cada tela de login: vale igual para quem entrou com senha, pela área
B2B ou com o Google, sem nenhum desses caminhos poder esquecer a checagem.

Depois de entrar com a senha, quem é da equipe:
- sem aplicativo cadastrado, cai na tela de cadastrar (mostra a chave e pede o
  primeiro código, para provar que o celular ficou certo);
- com aplicativo, cai na tela de digitar o código.
O "ok" fica na sessão, preso ao usuário, e vale até ela acabar.

"Lembrar este aparelho por 30 dias" deixa no navegador um cookie assinado com
o usuário e uma impressão do segredo do celular e da senha. Trocar a senha,
ou desligar e cadastrar o código de novo, invalida todos os aparelhos
lembrados; fora isso, o aparelho pula o código por 30 dias.

Perdeu o celular? No servidor: python manage.py desligar_dois_fatores <usuario>
"""
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from soar.seguranca import LIMITE_2FA, ip_do_cliente

from . import totp
from .models import DoisFatores

log = logging.getLogger('soar.seguranca')

CHAVE_OK = 'soar_2fa_ok'
CHAVE_NOVO_SEGREDO = 'soar_2fa_novo_segredo'

COOKIE_APARELHO = 'soar_2fa_aparelho'
SAL_APARELHO = 'soar.2fa.aparelho'
LEMBRAR_POR = timedelta(days=30)


def exigido(usuario):
    return bool(settings.DOIS_FATORES_EQUIPE and usuario.is_authenticated and usuario.is_staff)


def _impressao(usuario):
    """Muda quando muda a senha ou o segredo do celular: aí o aparelho lembrado deixa de valer."""
    cadastro = DoisFatores.objects.filter(usuario=usuario).first()
    if cadastro is None:
        return None
    return hashlib.sha256('{}|{}'.format(cadastro.segredo, usuario.password).encode()).hexdigest()[:32]


def aparelho_lembrado(request):
    valor = request.COOKIES.get(COOKIE_APARELHO)
    if not valor:
        return False
    try:
        dados = signing.loads(valor, salt=SAL_APARELHO, max_age=LEMBRAR_POR)
    except signing.BadSignature:      # adulterado ou passou dos 30 dias
        return False
    impressao = _impressao(request.user)
    return impressao is not None and dados == {'u': request.user.pk, 'i': impressao}


def lembrar_aparelho(resposta, usuario):
    resposta.set_cookie(
        COOKIE_APARELHO,
        signing.dumps({'u': usuario.pk, 'i': _impressao(usuario)}, salt=SAL_APARELHO),
        max_age=int(LEMBRAR_POR.total_seconds()), httponly=True, samesite='Lax',
        secure=settings.SESSION_COOKIE_SECURE)


def verificado(request):
    if request.session.get(CHAVE_OK) == request.user.pk:
        return True
    if aparelho_lembrado(request):
        # aparelho lembrado: vale para esta sessão inteira, sem pedir de novo
        request.session[CHAVE_OK] = request.user.pk
        return True
    return False


def pendente(request):
    """Esta sessão ainda precisa passar pelo código antes do painel?"""
    return exigido(request.user) and not verificado(request)


def _marcar_verificado(request):
    # Troca a chave da sessão ao subir de nível, como o login faz: um id de
    # sessão que tenha vazado antes do código não vale depois dele.
    request.session.cycle_key()
    request.session[CHAVE_OK] = request.user.pk
    request.session.pop(CHAVE_NOVO_SEGREDO, None)


def _proxima(request):
    destino = request.POST.get('next') or request.GET.get('next') or ''
    if destino and url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return destino
    return reverse('admin:index')


@login_required
def dois_fatores(request):
    """Cadastrar o aplicativo (primeira vez) ou digitar o código."""
    usuario = request.user
    if not usuario.is_staff:
        return redirect('contas:minha_conta')
    if not exigido(usuario) or verificado(request):
        # Com o código desligado (SOAR_2FA_EQUIPE), a tela não tem o que pedir.
        return redirect(_proxima(request))

    cadastro = DoisFatores.objects.filter(usuario=usuario).first()
    configurando = cadastro is None
    if configurando:
        segredo = request.session.get(CHAVE_NOVO_SEGREDO)
        if not segredo:
            segredo = totp.novo_segredo()
            request.session[CHAVE_NOVO_SEGREDO] = segredo
    else:
        segredo = cadastro.segredo

    erro = ''
    if request.method == 'POST':
        if LIMITE_2FA.estourou(request, usuario.pk):
            log.warning('2fa bloqueado por limite: usuario=%r ip=%s',
                        usuario.get_username(), ip_do_cliente(request))
            erro = 'Muitos códigos errados seguidos. Espere 15 minutos e tente de novo.'
        else:
            ultimo = 0 if configurando else cadastro.ultimo_passo
            passo = totp.conferir(segredo, request.POST.get('codigo', ''), ultimo)
            if passo is None:
                LIMITE_2FA.registrar(request, usuario.pk)
                log.warning('2fa codigo errado: usuario=%r ip=%s',
                            usuario.get_username(), ip_do_cliente(request))
                erro = 'Código não confere. Confira se é o da conta "Soar Operadora" no ' \
                       'aplicativo e se o relógio do celular está certo.'
            else:
                LIMITE_2FA.limpar(request, usuario.pk)
                if configurando:
                    DoisFatores.objects.create(usuario=usuario, segredo=segredo,
                                               ultimo_passo=passo)
                    log.info('2fa ativado: usuario=%r ip=%s',
                             usuario.get_username(), ip_do_cliente(request))
                    messages.success(request, 'Verificação em duas etapas ligada. Daqui para '
                                              'frente o painel pede o código do celular.')
                else:
                    cadastro.ultimo_passo = passo
                    cadastro.save(update_fields=['ultimo_passo'])
                    log.info('2fa ok: usuario=%r ip=%s',
                             usuario.get_username(), ip_do_cliente(request))
                _marcar_verificado(request)
                resposta = redirect(_proxima(request))
                if request.POST.get('lembrar'):
                    lembrar_aparelho(resposta, usuario)
                    log.info('2fa aparelho lembrado por 30 dias: usuario=%r ip=%s',
                             usuario.get_username(), ip_do_cliente(request))
                return resposta

    return render(request, 'contas/dois_fatores.html', {
        'configurando': configurando,
        'chave': totp.segredo_em_grupos(segredo) if configurando else '',
        'link_app': totp.link_do_aplicativo(segredo, usuario.get_username()) if configurando else '',
        'erro': erro,
        'next': request.POST.get('next') or request.GET.get('next', ''),
    })
