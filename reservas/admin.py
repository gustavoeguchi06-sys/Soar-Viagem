from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'destino', 'nome_do_cliente', 'pessoas',
                    'acomodacao', 'status', 'criado_em']
    list_filter = ['status', 'destino', 'acomodacao']
    list_editable = ['status']
    search_fields = ['usuario__first_name', 'usuario__username', 'usuario__email',
                     'destino__nome', 'telefone']
    date_hierarchy = 'criado_em'
    autocomplete_fields = ['destino']
    readonly_fields = ['criado_em', 'atualizado_em', 'preco_estimado', 'saida']
    fieldsets = [
        ('Pedido', {'fields': ['usuario', 'destino', 'acomodacao', 'pessoas', 'telefone',
                               'observacao']}),
        ('Situação', {'fields': ['status']}),
        ('Registro do momento do pedido', {
            'fields': ['preco_estimado', 'saida', 'criado_em', 'atualizado_em'],
            'description': 'Guardado automaticamente quando o cliente pediu a reserva.',
        }),
    ]

    @admin.display(description='Cliente', ordering='usuario__first_name')
    def nome_do_cliente(self, reserva):
        return reserva.usuario.get_full_name() or reserva.usuario.username

    @admin.display(description='Código')
    def codigo(self, reserva):
        return reserva.codigo
