"""Deixa os templates saberem quais botões de fora do site devem aparecer."""
from django.conf import settings

from . import google


def google_login(request):
    return {'google_login_ativo': google.configurado()}


def sistema_reservas(request):
    return {'sistema_reservas_url': settings.SISTEMA_RESERVAS_URL}


def site_em_andamento(request):
    """A tela "Site em andamento!" aparece para todo mundo, menos o dono e a equipe."""
    equipe = request.user.is_authenticated and request.user.is_staff
    return {'site_em_andamento': settings.SITE_EM_ANDAMENTO and not equipe}
