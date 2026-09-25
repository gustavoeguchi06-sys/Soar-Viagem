"""As agências parceiras (B2B) no painel do dono.

O dono confere o CNPJ e o CADASTUR e marca "Aprovado" direto na lista.
"""
from django.contrib import admin

from .models import PerfilAgente


@admin.register(PerfilAgente)
class PerfilAgenteAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'cnpj_mascara', 'cadastur', 'responsavel',
                    'email', 'whatsapp', 'aprovado', 'criado_em']
    list_display_links = ['razao_social']
    list_editable = ['aprovado']
    list_filter = ['aprovado']
    search_fields = ['razao_social', 'cnpj', 'cadastur',
                     'usuario__first_name', 'usuario__email', 'usuario__username']
    readonly_fields = ['criado_em']
    list_per_page = 30

    fieldsets = [
        ('Agência', {'fields': ['usuario', 'razao_social', 'cnpj', 'cadastur', 'whatsapp']}),
        ('Situação', {'fields': ['aprovado', 'criado_em']}),
    ]

    @admin.display(description='CNPJ')
    def cnpj_mascara(self, obj):
        return obj.cnpj_formatado

    @admin.display(description='Responsável')
    def responsavel(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.usuario.email
