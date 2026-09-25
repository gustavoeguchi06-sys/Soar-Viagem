"""Cadastro de destinos e hospedagens no painel do dono.

Duas decisões guiam este arquivo:

**Preço se edita na lista.** Corrigir a diária de seis destinos abrindo seis
formulários e salvando seis vezes é o tipo de tarefa que o dono deixa para
depois — e o site fica com preço velho. Com `list_editable`, a lista vira uma
planilha: digita, salva uma vez.

**O formulário do destino é longo, então ele é dobrado.** Só a primeira seção
(o catálogo) fica aberta; o resto da página de viagem abre quando o dono quiser
mexer. Cadastrar um destino novo é preencher o primeiro bloco e salvar — o
resto a página preenche sozinha com o texto padrão da operadora.
"""
import re
from decimal import Decimal

from django import forms
from django.contrib import admin
from django.core.validators import DecimalValidator
from django.db import models
from django.utils.html import format_html

from .models import (Destino, DestaqueViagem, DiaRoteiro, Hospedagem, ImagemDestino,
                     ImagemHospedagem, PerguntaFrequente, Saida, SlideInicio)

TEXTO_CURTO = {models.TextField: {'widget': forms.Textarea(attrs={'rows': 4})}}


class CampoPreco(forms.DecimalField):
    """Preço em reais do jeito brasileiro: ponto nos milhares, vírgula nos centavos.

    O campo numérico do navegador lia "6,500" como 6,5 e reclamava das casas
    decimais. Aqui o dono digita "6.500,00", "6500" ou "R$ 6.500" e tudo vira
    Decimal('6500.00'). Na tela, o valor guardado aparece como "6.500,00".
    """
    widget = forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': '0,00',
                                    'class': 'preco-brl', 'style': 'width: 9em'})
    default_error_messages = {
        'invalid': 'Digite o preço como 6.500,00: ponto nos milhares, vírgula nos centavos.',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for validador in self.validators:
            if isinstance(validador, DecimalValidator):
                validador.messages = {
                    **validador.messages,
                    'max_decimal_places': 'A vírgula é só para os centavos: use no máximo '
                                          '%(max)s casas (ex.: 6.500,00, não 6,500).',
                }

    def prepare_value(self, value):
        if isinstance(value, Decimal):
            inteiro, centavos = f'{value:,.2f}'.split('.')
            return inteiro.replace(',', '.') + ',' + centavos
        return value

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace('R$', '').replace(' ', '')
            if ',' in value:
                value = value.replace('.', '').replace(',', '.')
            elif value.count('.') > 1 or re.fullmatch(r'\d{1,3}(\.\d{3})+', value or ''):
                value = value.replace('.', '')
        return super().to_python(value)


PRECO_BRL = {models.DecimalField: {'form_class': CampoPreco}}


def miniatura(imagem, alt=''):
    """Uma foto pequena para a lista, ou um aviso de que falta foto."""
    if not imagem:
        return format_html('<span class="miniatura miniatura--vazia">sem foto</span>')
    return format_html('<img class="miniatura" src="{}" alt="{}">', imagem.url, alt)


# --------------------------------------------------------------------------- #
# Blocos embutidos no formulário do destino
# --------------------------------------------------------------------------- #

class ImagemDestinoInline(admin.TabularInline):
    model = ImagemDestino
    extra = 1
    fields = ['imagem', 'previa', 'legenda']
    readonly_fields = ['previa']
    verbose_name = 'foto'
    verbose_name_plural = 'Fotos da galeria'

    @admin.display(description='Prévia')
    def previa(self, obj):
        return miniatura(obj.imagem, obj.legenda)


class DestaqueViagemInline(admin.TabularInline):
    model = DestaqueViagem
    extra = 0
    fields = ['ordem', 'texto']
    verbose_name = 'destaque'
    verbose_name_plural = 'Destaques da viagem (o que a pessoa vai conhecer)'


class DiaRoteiroInline(admin.StackedInline):
    model = DiaRoteiro
    extra = 0
    fields = ['ordem', 'titulo', 'resumo', 'detalhe', 'imagem']
    formfield_overrides = {**TEXTO_CURTO, **PRECO_BRL}
    verbose_name = 'dia'
    verbose_name_plural = 'Roteiro dia a dia'
    classes = ['collapse']


class PerguntaFrequenteInline(admin.TabularInline):
    model = PerguntaFrequente
    extra = 0
    fields = ['ordem', 'pergunta', 'resposta']
    formfield_overrides = {models.TextField: {'widget': forms.Textarea(attrs={'rows': 2})}}
    verbose_name = 'pergunta'
    verbose_name_plural = 'Perguntas frequentes'
    classes = ['collapse']


class HospedagemInline(admin.TabularInline):
    model = Hospedagem
    extra = 0
    fields = ['nome', 'endereco', 'pacote_completo']
    show_change_link = True
    verbose_name = 'hospedagem'
    verbose_name_plural = 'Hospedagens deste destino (clique em "alterar" para fotos e endereço)'


# --------------------------------------------------------------------------- #
# Destino
# --------------------------------------------------------------------------- #

class SaidaInline(admin.TabularInline):
    """As datas de saída do destino, uma por linha, com calendário."""

    model = Saida
    extra = 1
    fields = ['data_ida', 'data_volta', 'vagas']
    formfield_overrides = {
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')},
    }
    verbose_name = 'saída'
    verbose_name_plural = ('Datas de saída (o site mostra todas as que ainda vão acontecer; '
                           'as que já passaram somem sozinhas)')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for campo in ('data_ida', 'data_volta'):
            formset.form.base_fields[campo].input_formats = ['%Y-%m-%d']
        return formset


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ['capa', 'nome', 'regiao', 'preco_base', 'preco_medio_diaria',
                    'saidas_no_site', 'destaque', 'soar_60', 'situacao', 'no_site']
    list_display_links = ['nome']
    list_editable = ['preco_base', 'preco_medio_diaria', 'destaque', 'soar_60']
    list_filter = ['destaque', 'soar_60', 'regiao']
    search_fields = ['nome', 'regiao', 'descricao']
    prepopulated_fields = {'slug': ['nome']}
    formfield_overrides = {**TEXTO_CURTO, **PRECO_BRL}
    save_on_top = True
    list_per_page = 30
    readonly_fields = ['previa_capa', 'criado_em']
    inlines = [SaidaInline, HospedagemInline, ImagemDestinoInline, DestaqueViagemInline,
               DiaRoteiroInline, PerguntaFrequenteInline]

    fieldsets = [
        ('O destino no catálogo', {
            'fields': ['nome', 'slug', 'regiao', 'descricao',
                       'imagem_capa', 'previa_capa', 'melhor_epoca', 'destaque', 'soar_60'],
            'description': 'O mínimo para o destino existir. A operadora só trabalha '
                           'no Brasil, então o país é sempre Brasil. O resto da página '
                           'tem texto padrão e pode ficar para depois.',
        }),
        ('Preços', {
            'fields': ['preco_base', 'preco_medio_diaria'],
            'description': 'O preço por pessoa é o que abre o card de reserva. '
                           'Sem nenhum dos dois, a página mostra “sob consulta”.',
        }),
        ('Capa da página de viagem', {
            'classes': ['collapse'],
            'fields': ['selo', 'subtitulo', 'estado'],
            'description': 'Tudo opcional. Em branco, a página usa o texto padrão da Soar.',
        }),
        ('Textos da página', {
            'classes': ['collapse'],
            'fields': ['hospedagem_sub', 'incluso', 'informacoes'],
            'description': 'Nos dois últimos, escreva um item por linha.',
        }),
        ('Registro', {
            'classes': ['collapse'],
            'fields': ['criado_em'],
        }),
    ]

    @admin.display(description='')
    def capa(self, destino):
        return miniatura(destino.imagem_capa, destino.nome)

    @admin.display(description='Foto de capa como fica no site')
    def previa_capa(self, destino):
        if not destino.imagem_capa:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem capa: a página usa uma ilustração da Soar.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="{}">',
                           destino.imagem_capa.url, destino.nome)

    @admin.display(description='Saídas')
    def saidas_no_site(self, destino):
        futuras = list(destino.saidas_futuras)
        if not futuras:
            return format_html('<span class="etiqueta etiqueta--fila">nenhuma</span>')
        proxima = futuras[0].data_ida.strftime('%d/%m/%Y')
        if len(futuras) == 1:
            return format_html('1 saída, em {}', proxima)
        return format_html('{} saídas, a próxima em {}', len(futuras), proxima)

    @admin.display(description='Situação')
    def situacao(self, destino):
        if destino.preco_base or destino.preco_medio_diaria:
            return format_html('<span class="etiqueta etiqueta--confirmada">no ar</span>')
        return format_html('<span class="etiqueta etiqueta--fila">sem preço</span>')

    @admin.display(description='')
    def no_site(self, destino):
        return format_html('<a href="{}" target="_blank" rel="noopener">abrir &#8599;</a>',
                           destino.get_absolute_url())


# --------------------------------------------------------------------------- #
# Hospedagem
# --------------------------------------------------------------------------- #

class ImagemHospedagemInline(admin.TabularInline):
    model = ImagemHospedagem
    extra = 1
    fields = ['imagem', 'previa', 'legenda']
    readonly_fields = ['previa']
    verbose_name = 'foto'
    verbose_name_plural = 'Fotos da hospedagem'

    @admin.display(description='Prévia')
    def previa(self, obj):
        return miniatura(obj.imagem, obj.legenda)


@admin.register(Hospedagem)
class HospedagemAdmin(admin.ModelAdmin):
    list_display = ['foto', 'nome', 'destino', 'endereco', 'pacote_completo']
    list_display_links = ['nome']
    list_editable = ['pacote_completo']
    list_filter = ['pacote_completo', 'destino']
    search_fields = ['nome', 'destino__nome']
    autocomplete_fields = ['destino']
    formfield_overrides = {**TEXTO_CURTO, **PRECO_BRL}
    save_on_top = True
    list_per_page = 30
    readonly_fields = ['previa_imagem']
    inlines = [ImagemHospedagemInline]

    fieldsets = [
        ('A hospedagem', {
            'fields': ['destino', 'nome', 'endereco', 'pacote_completo'],
        }),
        ('Foto', {
            'fields': ['imagem', 'previa_imagem'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('destino')

    @admin.display(description='')
    def foto(self, hospedagem):
        return miniatura(hospedagem.imagem, hospedagem.nome)

    @admin.display(description='Foto principal')
    def previa_imagem(self, hospedagem):
        if not hospedagem.imagem:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="{}">',
                           hospedagem.imagem.url, hospedagem.nome)


# --------------------------------------------------------------------------- #
# Fotos do topo da página inicial
# --------------------------------------------------------------------------- #

@admin.register(SlideInicio)
class SlideInicioAdmin(admin.ModelAdmin):
    """As fotos que giram no topo da página inicial."""

    list_display = ['foto', 'legenda', 'ordem', 'ativo']
    list_display_links = ['foto', 'legenda']
    list_editable = ['ordem', 'ativo']
    fields = ['imagem', 'previa', 'legenda', 'ordem', 'ativo']
    readonly_fields = ['previa']

    @admin.display(description='')
    def foto(self, slide):
        return miniatura(slide.imagem, slide.legenda)

    @admin.display(description='Como fica')
    def previa(self, slide):
        if not slide.imagem:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto: a página usa as fotos de exemplo do site.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">', slide.imagem.url)
