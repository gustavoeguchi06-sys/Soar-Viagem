"""Deixa os templates saberem se o botão do Google deve aparecer."""
from . import google


def google_login(request):
    return {'google_login_ativo': google.configurado()}
