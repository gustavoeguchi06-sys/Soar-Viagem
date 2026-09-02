from django.urls import path

from . import views

app_name = 'reservas'

urlpatterns = [
    path('reservar/<slug:slug>/', views.nova, name='nova'),
    path('reservas/<int:pk>/cancelar/', views.cancelar, name='cancelar'),
]
