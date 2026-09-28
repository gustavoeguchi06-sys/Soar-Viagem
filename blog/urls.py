from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.indice, name='indice'),
    # antes do <slug>, senão "novidades" seria lido como nome de artigo
    path('novidades/', views.inscrever, name='inscrever'),
    path('novidades/confirmar/<str:token>/', views.confirmar, name='confirmar'),
    path('<slug:slug>/', views.artigo, name='artigo'),
]
