from django.urls import path

from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.home, name='home'),
    path('destinos/', views.lista_destinos, name='lista'),
    path('destinos/<slug:slug>/', views.detalhe_destino, name='detalhe'),
]
