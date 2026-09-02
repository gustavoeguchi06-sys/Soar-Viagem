from django.contrib import admin

from .models import (Destino, DestaqueViagem, DiaRoteiro, Hospedagem, ImagemDestino,
                     ImagemHospedagem, PerguntaFrequente)


class ImagemDestinoInline(admin.TabularInline):
    model = ImagemDestino
    extra = 1
    verbose_name_plural = 'Fotos do destino (galeria da página)'


class DestaqueViagemInline(admin.TabularInline):
    model = DestaqueViagem
    extra = 0
    fields = ['ordem', 'texto']
    verbose_name_plural = 'Destaques da viagem (o que a pessoa vai conhecer)'


class DiaRoteiroInline(admin.StackedInline):
    model = DiaRoteiro
    extra = 0
    fields = ['ordem', 'titulo', 'resumo', 'detalhe', 'imagem']
    verbose_name_plural = 'Roteiro dia a dia'


class PerguntaFrequenteInline(admin.TabularInline):
    model = PerguntaFrequente
    extra = 0
    fields = ['ordem', 'pergunta', 'resposta']
    verbose_name_plural = 'Perguntas frequentes'


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
    inlines = [ImagemDestinoInline, DestaqueViagemInline, DiaRoteiroInline,
               PerguntaFrequenteInline, HospedagemInline]
    fieldsets = [
        ('O destino', {
            'fields': ['nome', 'slug', 'pais', 'continente', 'descricao', 'imagem_capa',
                       'preco_medio_diaria', 'melhor_epoca', 'destaque'],
        }),
        ('Sobre a viagem — capa', {
            'fields': ['selo', 'subtitulo', 'regiao', 'estado'],
            'description': 'Tudo opcional. Em branco, a página usa o texto padrão da Soar.',
        }),
        ('Sobre a viagem — datas e preço', {
            'fields': ['periodo', 'mes_ano', 'dias', 'noites', 'proxima_saida', 'vagas',
                       'preco_base'],
        }),
        ('Sobre a viagem — textos', {
            'fields': ['hospedagem_sub', 'incluso', 'informacoes'],
        }),
    ]


class ImagemHospedagemInline(admin.TabularInline):
    model = ImagemHospedagem
    extra = 1


@admin.register(Hospedagem)
class HospedagemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'destino', 'tipo', 'preco_diaria', 'disponivel']
    list_filter = ['tipo', 'disponivel', 'destino']
    search_fields = ['nome', 'destino__nome']
    inlines = [ImagemHospedagemInline]
