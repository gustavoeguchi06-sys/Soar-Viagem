from django.urls import path

from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.home, name='home'),
    path('soar-60/', views.soar_60, name='soar_60'),
    path('destinos/', views.lista_destinos, name='lista'),
    path('calendario/', views.calendario, name='calendario'),
    path('destinos/<slug:slug>/', views.detalhe_destino, name='detalhe'),
]
