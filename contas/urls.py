from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'contas'

# Recuperação de senha: as telas são as do próprio Django, com os templates da
# Soar. Antes não existia caminho nenhum — quem esquecia a senha perdia a conta
# e o histórico de reservas, o que empurra todo mundo para senha fácil.
#
# O formulário do Django não diz se o e-mail existe: manda a mensagem quando
# existe e fica quieto quando não, sempre com a mesma tela. É de propósito.
urlpatterns = [
    path('entrar/', views.entrar, name='entrar'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('cadastro/confirmar/<uidb64>/<token>/', views.ativar, name='ativar'),
    path('sair/', views.sair, name='sair'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),

    # Dados pessoais (LGPD)
    path('privacidade/', views.privacidade, name='privacidade'),
    path('minha-conta/meus-dados/', views.meus_dados, name='meus_dados'),
    path('minha-conta/excluir/', views.excluir_conta, name='excluir_conta'),

    # Esqueci minha senha
    path('senha/', auth_views.PasswordResetView.as_view(
        template_name='contas/senha_pedir.html',
        email_template_name='contas/email/senha_reset.txt',
        subject_template_name='contas/email/senha_reset_assunto.txt',
        success_url=reverse_lazy('contas:password_reset_done'),
    ), name='senha_reset'),
    path('senha/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='contas/senha_enviado.html',
    ), name='password_reset_done'),
    path('senha/nova/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='contas/senha_nova.html',
        success_url=reverse_lazy('contas:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('senha/pronto/', auth_views.PasswordResetCompleteView.as_view(
        template_name='contas/senha_pronto.html',
    ), name='password_reset_complete'),
]
