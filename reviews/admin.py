from django.contrib import admin

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['nome_autor', 'destino', 'nota', 'criado_em']
    list_filter = ['nota', 'destino']
    search_fields = ['nome_autor', 'comentario', 'destino__nome']
    date_hierarchy = 'criado_em'
