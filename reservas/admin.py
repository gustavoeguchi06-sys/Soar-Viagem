"""As reservas no painel do dono.

Esta é a tela de trabalho da operadora, não um cadastro: a reserva chega como
pedido e alguém precisa ligar para o cliente, confirmar a vaga e combinar o
pagamento. Por isso a lista é montada em volta desse ritmo — as pendentes sobem
para o topo, o telefone vira um link de WhatsApp e dá para confirmar várias de
uma vez pela ação em massa, sem abrir uma por uma.
"""
import re

from django.contrib import admin, messages
from django.db.models import Case, IntegerField, Value, When
from django.utils.formats import number_format
from django.utils.html import format_html

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'situacao', 'destino', 'cliente', 'contato',
                    'pessoas', 'acomodacao', 'total', 'agencia', 'status', 'criado_em']
    list_display_links = ['codigo']
    list_editable = ['status']
    list_filter = ['status', 'destino', 'acomodacao', 'agencia']
    search_fields = ['usuario__first_name', 'usuario__username', 'usuario__email',
                     'destino__nome', 'telefone']
    date_hierarchy = 'criado_em'
    autocomplete_fields = ['destino']
    actions = ['confirmar', 'cancelar']
    save_on_top = True
    list_per_page = 40
    readonly_fields = ['criado_em', 'atualizado_em', 'preco_estimado', 'saida',
                       'total', 'contato']

    fieldsets = [
        ('Situação', {
            'fields': ['status'],
            'description': 'O cliente vê esta situação em “Minha conta”.',
        }),
        ('Quem pediu', {
            'fields': ['usuario', 'contato', 'telefone', 'observacao'],
        }),
        ('A viagem pedida', {
            'fields': ['destino', 'acomodacao', 'pessoas'],
        }),
        ('Agência parceira', {
            'fields': ['agencia', 'nota_agencia'],
            'description': 'A agência escolhida aqui passa a ver esta reserva no painel '
                           'dela e pode atender o cliente. Em branco, só a Soar vê.',
        }),
        ('Registro do momento do pedido', {
            'fields': ['preco_estimado', 'total', 'saida', 'criado_em', 'atualizado_em'],
            'description': 'Guardado automaticamente quando o cliente pediu a reserva. '
                           'Se a tabela de preços mudar depois, o que foi combinado '
                           'com esta pessoa não se perde.',
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('destino', 'usuario', 'agencia')

    def get_ordering(self, request):
        """Pendente primeiro: é a fila de quem está esperando resposta.

        A ordem sai de uma expressão, e não de uma anotação, porque o
        `ModelAdmin.get_queryset` aplica o `order_by` antes de qualquer
        `annotate` nosso — um nome de anotação aqui quebraria a consulta. O
        `Case` só olha para `status`, que é campo de verdade, então funciona nos
        dois lugares. Clicar no cabeçalho de uma coluna continua reordenando.
        """
        espera_primeiro = Case(
            When(status='pendente', then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ).asc()
        return [espera_primeiro, '-criado_em']

    @admin.display(description='Código', ordering='pk')
    def codigo(self, reserva):
        return reserva.codigo

    @admin.display(description='', ordering='status')
    def situacao(self, reserva):
        return format_html('<span class="etiqueta etiqueta--{}">{}</span>',
                           reserva.status, reserva.get_status_display())

    @admin.display(description='Cliente', ordering='usuario__first_name')
    def cliente(self, reserva):
        if reserva.usuario is None:
            return 'Cliente removido'
        return reserva.usuario.get_full_name() or reserva.usuario.username

    @admin.display(description='Contato')
    def contato(self, reserva):
        """O telefone como link de WhatsApp — um clique e a conversa abre."""
        if not reserva.telefone:
            return '-'
        numeros = re.sub(r'\D', '', reserva.telefone)
        if len(numeros) < 10:
            return reserva.telefone
        if not numeros.startswith('55'):
            numeros = '55' + numeros
        return format_html('<a href="https://wa.me/{}" target="_blank" rel="noopener">{}</a>',
                           numeros, reserva.telefone)

    @admin.display(description='Total estimado')
    def total(self, reserva):
        if reserva.total_estimado is None:
            return '-'
        # number_format respeita o pt-br do projeto: 1.234,50 e não 1,234.50.
        return 'R$ {}'.format(number_format(reserva.total_estimado, decimal_pos=2,
                                            force_grouping=True))

    @admin.action(description='Confirmar as reservas selecionadas')
    def confirmar(self, request, queryset):
        total = queryset.update(status='confirmada')
        self.message_user(request, f'{total} reserva(s) confirmada(s). '
                                   'Avise o cliente pelo WhatsApp.', messages.SUCCESS)

    @admin.action(description='Cancelar as reservas selecionadas')
    def cancelar(self, request, queryset):
        total = queryset.update(status='cancelada')
        self.message_user(request, f'{total} reserva(s) cancelada(s).', messages.WARNING)
