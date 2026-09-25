from django.urls import path

from . import views

app_name = 'agencia'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('reservas/', views.reservas, name='reservas'),
    path('reservas/<int:pk>/', views.reserva, name='reserva'),
    path('orcamentos/', views.orcamentos, name='orcamentos'),
    path('orcamentos/novo/', views.orcamento_novo, name='orcamento_novo'),
    path('orcamentos/<int:pk>/', views.orcamento_editar, name='orcamento_editar'),
    path('minha-agencia/', views.minha_agencia, name='minha_agencia'),
]
