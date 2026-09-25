"""Os orçamentos das agências, vistos pelo dono.

O dono enxerga os orçamentos de todas as agências para acompanhar as vendas
B2B. Quem cria e mexe no orçamento é a agência, no painel dela.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Orcamento


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'agencia', 'cliente_nome', 'destino', 'saida_texto',
                    'pessoas', 'valor', 'situacao', 'criado_em']
    list_display_links = ['codigo']
    list_filter = ['status', 'agencia', 'destino']
    search_fields = ['cliente_nome', 'cliente_email', 'cliente_telefone',
                     'agencia__razao_social', 'destino__nome']
    date_hierarchy = 'criado_em'
    readonly_fields = ['saida_texto', 'criado_em', 'atualizado_em']
    list_per_page = 40

    fieldsets = [
        ('Agência e situação', {'fields': ['agencia', 'status']}),
        ('Cliente', {'fields': ['cliente_nome', 'cliente_telefone', 'cliente_email']}),
        ('Viagem', {'fields': ['destino', 'saida', 'saida_texto', 'acomodacao', 'pessoas',
                               'valor', 'validade', 'observacoes']}),
        ('Registro', {'classes': ['collapse'], 'fields': ['criado_em', 'atualizado_em']}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agencia', 'destino')

    @admin.display(description='Código', ordering='pk')
    def codigo(self, orcamento):
        return orcamento.codigo

    @admin.display(description='Situação', ordering='status')
    def situacao(self, orcamento):
        cor = {'enviado': 'pendente', 'aceito': 'confirmada', 'recusado': 'cancelada'}
        return format_html('<span class="etiqueta etiqueta--{}">{}</span>',
                           cor.get(orcamento.status, 'pendente'), orcamento.get_status_display())
