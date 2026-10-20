"""Deixa os templates saberem quais botões de fora do site devem aparecer."""
import hmac

from django.conf import settings

from . import google


def google_login(request):
    return {'google_login_ativo': google.configurado()}


def sistema_reservas(request):
    return {'sistema_reservas_url': settings.SISTEMA_RESERVAS_URL}


def site_em_construcao(request):
    """A tela "Site em Construção" aparece para todo mundo, menos o dono e a equipe.

    O login também fica coberto, menos pelo link secreto
    /entrar/?acesso=<SITE_EM_CONSTRUCAO_ACESSO>, que só o dono e quem cuida do
    site têm. Depois de entrar, a equipe não vê mais a tela.
    """
    equipe = request.user.is_authenticated and request.user.is_staff
    return {'site_em_construcao': settings.SITE_EM_CONSTRUCAO and not equipe
            and not _login_pelo_link_secreto(request)}


def _login_pelo_link_secreto(request):
    codigo = settings.SITE_EM_CONSTRUCAO_ACESSO
    rota = getattr(request, 'resolver_match', None)
    if not codigo or rota is None or rota.view_name != 'contas:entrar':
        return False
    return hmac.compare_digest(request.GET.get('acesso', ''), codigo)


def analytics(request):
    """ID do Google Analytics para o base.html, ou vazio para não carregar nada.

    Fica de fora quem é da equipe (o dono navegando no próprio site inflaria os
    números) e o painel do dono, que nem usa o base.html, mas fica garantido.
    """
    ga = settings.GA_ID
    if not ga:
        return {'analytics_id': ''}
    equipe = request.user.is_authenticated and request.user.is_staff
    no_painel = request.path.startswith('/painel/')
    return {'analytics_id': '' if equipe or no_painel else ga}
