from django.contrib import admin, messages

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['nome_autor', 'destino', 'nota', 'publicada', 'criado_em']
    list_filter = ['publicada', 'nota', 'destino']
    search_fields = ['nome_autor', 'comentario', 'destino__nome', 'autor__email']
    date_hierarchy = 'criado_em'
    actions = ['publicar', 'despublicar']
    readonly_fields = ['autor', 'nome_autor', 'ip', 'criado_em']
    fieldsets = [
        ('Avaliação', {'fields': ['destino', 'nota', 'comentario', 'foto']}),
        ('Moderação', {
            'fields': ['publicada'],
            'description': 'A avaliação só aparece no site depois de publicada.',
        }),
        ('Quem enviou', {
            'fields': ['autor', 'nome_autor', 'ip', 'criado_em'],
            'description': 'Registrado no envio. Serve para apurar abuso.',
        }),
    ]

    def get_queryset(self, request):
        # As pendentes primeiro: é a fila de trabalho do dono.
        return super().get_queryset(request).order_by('publicada', '-criado_em')

    @admin.action(description='Publicar as avaliações selecionadas')
    def publicar(self, request, queryset):
        total = queryset.update(publicada=True)
        self.message_user(request, f'{total} avaliação(ões) publicada(s).', messages.SUCCESS)

    @admin.action(description='Tirar do ar as avaliações selecionadas')
    def despublicar(self, request, queryset):
        total = queryset.update(publicada=False)
        self.message_user(request, f'{total} avaliação(ões) fora do ar.', messages.WARNING)
