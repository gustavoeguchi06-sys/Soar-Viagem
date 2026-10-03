"""Deixa os templates saberem quais botões de fora do site devem aparecer."""
from django.conf import settings

from . import google


def google_login(request):
    return {'google_login_ativo': google.configurado()}


def sistema_reservas(request):
    return {'sistema_reservas_url': settings.SISTEMA_RESERVAS_URL}
