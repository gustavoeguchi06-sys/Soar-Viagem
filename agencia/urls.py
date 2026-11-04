from django.urls import path

from . import views

app_name = 'agencia'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('minha-agencia/', views.minha_agencia, name='minha_agencia'),
    path('orcamentos/', views.orcamentos, name='orcamentos'),
    path('orcamentos/<int:pk>/situacao/', views.orcamento_situacao, name='orcamento_situacao'),
    # O orçamento é feito no card da página da viagem, sem abrir o painel.
    path('orcamentos/criar/<slug:slug>/', views.orcamento_criar, name='orcamento_criar'),
    path('orcamentos/<int:pk>/pdf/', views.orcamento_pdf, name='orcamento_pdf'),
]
