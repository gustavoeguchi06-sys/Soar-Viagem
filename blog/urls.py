from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.indice, name='indice'),
    path('<slug:slug>/', views.artigo, name='artigo'),
]
