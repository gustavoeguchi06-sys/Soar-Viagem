"""Os orçamentos das agências, vistos pelo dono.

O dono enxerga os orçamentos de todas as agências para acompanhar as vendas
B2B. Quem cria o orçamento é só a agência, no card da página da viagem: no
painel não há como criar nem alterar um orçamento, só ver e marcar a situação
(aceito ou recusado). E só o dono vê esta lista, porque traz dados de cliente.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import AvisoAgente, Orcamento


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'agencia', 'cliente_nome', 'destino', 'saida_texto',
                    'pessoas', 'valor_brl', 'situacao', 'criado_em', 'valido_ate']
    list_display_links = ['codigo']
    list_filter = ['status', 'agencia', 'destino']
    search_fields = ['cliente_nome', 'cliente_email', 'cliente_telefone',
                     'agencia__razao_social', 'destino__nome']
    date_hierarchy = 'criado_em'
    # tudo fica só para ver; a única coisa que o dono muda é a situação
    readonly_fields = ['agencia', 'cliente_nome', 'cliente_telefone', 'cliente_email',
                       'destino', 'saida_texto', 'acomodacao_texto', 'pessoas', 'valor_brl',
                       'valido_ate', 'observacoes', 'criado_em', 'atualizado_em', 'enviado_em']
    list_per_page = 40

    fieldsets = [
        ('Agência e situação', {'fields': ['agencia', 'status']}),
        ('Cliente', {'fields': ['cliente_nome', 'cliente_telefone', 'cliente_email']}),
        ('Viagem', {'fields': ['destino', 'saida_texto', 'acomodacao_texto', 'pessoas',
                               'valor_brl', 'valido_ate', 'observacoes']}),
        ('Registro', {'classes': ['collapse'], 'fields': ['criado_em', 'atualizado_em',
                                                          'enviado_em']}),
    ]

    @admin.display(description='Acomodação')
    def acomodacao_texto(self, orcamento):
        return orcamento.acomodacao_texto

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agencia', 'destino')

    # orçamento nasce só no site, pela agência
    def has_add_permission(self, request):
        return False

    # só o dono
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    @admin.display(description='Código', ordering='pk')
    def codigo(self, orcamento):
        return orcamento.codigo

    @admin.display(description='Valor', ordering='valor')
    def valor_brl(self, orcamento):
        if orcamento.valor is None:
            return '-'
        inteiro, centavos = f'{orcamento.valor:,.2f}'.split('.')
        return 'R$ ' + inteiro.replace(',', '.') + ',' + centavos

    @admin.display(description='Situação', ordering='status')
    def situacao(self, orcamento):
        cor = {'enviado': 'pendente', 'aceito': 'confirmada', 'recusado': 'cancelada'}
        return format_html('<span class="etiqueta etiqueta--{}">{}</span>',
                           cor.get(orcamento.status, 'pendente'), orcamento.get_status_display())


@admin.register(AvisoAgente)
class AvisoAgenteAdmin(admin.ModelAdmin):
    """O pop-up que o agente vê ao entrar. Só o dono mexe."""
    list_display = ['titulo', 'previa_lista', 'no_ar', 'mostrar_ate', 'criado_em']
    list_display_links = ['titulo']
    fields = ['titulo', 'imagem', 'previa', 'link', 'ativo', 'mostrar_ate']
    readonly_fields = ['previa']

    @admin.display(description='Arte')
    def previa_lista(self, aviso):
        return format_html('<img class="miniatura" src="{}" alt="">', aviso.imagem.url) if aviso.imagem else '-'

    @admin.display(description='Como fica')
    def previa(self, aviso):
        if not aviso.imagem:
            return 'Escolha a arte e salve para ver aqui.'
        return format_html('<img src="{}" alt="" style="max-width:260px;border-radius:8px">',
                           aviso.imagem.url)

    @admin.display(description='Situação')
    def no_ar(self, aviso):
        if aviso == AvisoAgente.vigente():
            return format_html('<span class="etiqueta etiqueta--confirmada">aparecendo no login</span>')
        if not aviso.ativo:
            return format_html('<span class="etiqueta etiqueta--cancelada">desligado</span>')
        return format_html('<span class="etiqueta etiqueta--pendente">fora do prazo ou substituído</span>')

    def _dono(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_module_permission(self, request):
        return self._dono(request)

    def has_view_permission(self, request, obj=None):
        return self._dono(request)

    def has_add_permission(self, request):
        return self._dono(request)

    def has_change_permission(self, request, obj=None):
        return self._dono(request)

    def has_delete_permission(self, request, obj=None):
        return self._dono(request)

