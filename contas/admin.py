"""As agências parceiras (B2B) no painel do dono.

O dono confere o CNPJ e marca "Aprovado" direto na lista. A mesma agência
(o mesmo CNPJ) pode ter vários agentes: cada linha é um agente, com o nome
dele na frente, para o dono saber para quem está indicando o cliente. O
CADASTUR é o próprio CNPJ e não é mais digitado.
"""
from django.contrib import admin

from .models import PerfilAgente


@admin.register(PerfilAgente)
class PerfilAgenteAdmin(admin.ModelAdmin):
    list_display = ['responsavel', 'razao_social', 'cnpj_mascara', 'email', 'whatsapp',
                    'aprovado', 'criado_em']
    list_display_links = ['responsavel']
    list_editable = ['aprovado']
    list_filter = ['aprovado']
    search_fields = ['razao_social', 'cnpj', 'cadastur',
                     'usuario__first_name', 'usuario__email', 'usuario__username']
    readonly_fields = ['cadastur_igual_cnpj', 'criado_em']
    list_per_page = 30

    fieldsets = [
        ('Agente e agência', {'fields': ['usuario', 'razao_social', 'cnpj', 'cadastur_igual_cnpj',
                                         'whatsapp']}),
        ('Situação', {'fields': ['aprovado', 'criado_em']}),
    ]

    @admin.display(description='CNPJ')
    def cnpj_mascara(self, obj):
        return obj.cnpj_formatado

    @admin.display(description='Agente de viagens', ordering='usuario__first_name')
    def responsavel(self, obj):
        return obj.nome_agente

    @admin.display(description='CADASTUR')
    def cadastur_igual_cnpj(self, obj):
        return '{} (o mesmo do CNPJ)'.format(obj.cnpj_formatado) if obj.cnpj else '-'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.usuario.email
