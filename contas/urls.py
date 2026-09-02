from django.urls import path

from . import views

app_name = 'contas'

urlpatterns = [
    path('entrar/', views.entrar, name='entrar'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', views.sair, name='sair'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),
]
