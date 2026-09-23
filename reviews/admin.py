"""Moderação das avaliações no painel do dono.

A avaliação chega despublicada e fica numa fila: enquanto o dono não aprova,
ela não conta para a nota que aparece na vitrine. Por isso a lista abre com as
pendentes no topo e o trabalho todo cabe em duas ações em massa.
"""
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['miniatura', 'nome_autor', 'destino', 'estrelas', 'trecho',
                    'situacao', 'criado_em']
    list_display_links = ['nome_autor']
    list_filter = ['publicada', 'nota', 'destino']
    search_fields = ['nome_autor', 'comentario', 'destino__nome', 'autor__email']
    date_hierarchy = 'criado_em'
    actions = ['publicar', 'despublicar']
    list_per_page = 30
    readonly_fields = ['autor', 'nome_autor', 'ip', 'criado_em', 'previa_foto']

    fieldsets = [
        ('Moderação', {
            'fields': ['publicada'],
            'description': 'A avaliação só aparece no site, e só conta para a nota '
                           'do destino, depois de publicada.',
        }),
        ('A avaliação', {
            'fields': ['destino', 'nota', 'comentario', 'foto', 'previa_foto'],
        }),
        ('Quem enviou', {
            'classes': ['collapse'],
            'fields': ['autor', 'nome_autor', 'ip', 'criado_em'],
            'description': 'Registrado no envio. Serve para apurar abuso.',
        }),
    ]

    def get_queryset(self, request):
        # As pendentes primeiro: é a fila de trabalho do dono.
        return super().get_queryset(request).select_related('destino', 'autor')

    def get_ordering(self, request):
        return ['publicada', '-criado_em']

    @admin.display(description='')
    def miniatura(self, avaliacao):
        if not avaliacao.foto:
            return format_html('<span class="miniatura miniatura--vazia">sem foto</span>')
        return format_html('<img class="miniatura" src="{}" alt="">', avaliacao.foto.url)

    @admin.display(description='Nota', ordering='nota')
    def estrelas(self, avaliacao):
        return format_html('<span class="estrelas">{}</span>', avaliacao.estrelas)

    @admin.display(description='Comentário')
    def trecho(self, avaliacao):
        texto = avaliacao.comentario
        return texto if len(texto) <= 90 else texto[:90].rstrip() + '…'

    @admin.display(description='', ordering='publicada')
    def situacao(self, avaliacao):
        if avaliacao.publicada:
            return format_html('<span class="etiqueta etiqueta--publicada">no site</span>')
        return format_html('<span class="etiqueta etiqueta--fila">na fila</span>')

    @admin.display(description='Foto enviada')
    def previa_foto(self, avaliacao):
        if not avaliacao.foto:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">',
                           avaliacao.foto.url)

    @admin.action(description='Publicar as avaliações selecionadas')
    def publicar(self, request, queryset):
        total = queryset.update(publicada=True)
        self.message_user(request, f'{total} avaliação(ões) publicada(s).', messages.SUCCESS)

    @admin.action(description='Tirar do ar as avaliações selecionadas')
    def despublicar(self, request, queryset):
        total = queryset.update(publicada=False)
        self.message_user(request, f'{total} avaliação(ões) fora do ar.', messages.WARNING)
