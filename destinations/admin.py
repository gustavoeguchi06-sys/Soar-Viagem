from django.contrib import admin

from .models import Destino, Hospedagem, ImagemDestino, ImagemHospedagem


class ImagemDestinoInline(admin.TabularInline):
    model = ImagemDestino
    extra = 1


class HospedagemInline(admin.TabularInline):
    model = Hospedagem
    extra = 0
    fields = ['nome', 'tipo', 'preco_diaria', 'disponivel']
    show_change_link = True


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'pais', 'continente', 'preco_medio_diaria', 'destaque', 'criado_em']
    list_filter = ['continente', 'destaque', 'pais']
    search_fields = ['nome', 'pais', 'descricao']
    prepopulated_fields = {'slug': ['nome']}
    inlines = [ImagemDestinoInline, HospedagemInline]


class ImagemHospedagemInline(admin.TabularInline):
    model = ImagemHospedagem
    extra = 1


@admin.register(Hospedagem)
class HospedagemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'destino', 'tipo', 'preco_diaria', 'disponivel']
    list_filter = ['tipo', 'disponivel', 'destino']
    search_fields = ['nome', 'destino__nome']
    inlines = [ImagemHospedagemInline]
