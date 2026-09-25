"""Blog Soar no painel do dono.

O que guia esta tela: o dono não é da área de tecnologia, então tudo que dá
para errar digitando vira clique. A data de publicação é um calendário, os
meses de melhor época são caixinhas, o ícone e a cor são listas, o endereço
do artigo e o tempo de leitura se preenchem sozinhos.
"""
from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.utils import formats
from django.utils.html import format_html

from destinations.admin import miniatura

from .models import MESES, Artigo, Atracao, Categoria, Inscricao, Secao

CALENDARIO = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class MesesField(forms.MultipleChoiceField):
    """Caixinhas de Jan a Dez, guardadas no banco como "5,6,7"."""

    def __init__(self, **kwargs):
        super().__init__(choices=MESES, required=False,
                         widget=forms.CheckboxSelectMultiple(attrs={'class': 'meses-escolha'}),
                         **kwargs)

    def prepare_value(self, value):
        if isinstance(value, str):
            return [m for m in value.split(',') if m]
        return value

    def clean(self, value):
        return ','.join(sorted(super().clean(value), key=int))

    def has_changed(self, initial, data):
        return super().has_changed(self.prepare_value(initial) or [], data)


class SecaoForm(forms.ModelForm):
    melhores_meses = MesesField(label='Meses de ótima época',
                                help_text='Opcional. Marque para mostrar a faixa dos 12 meses.')
    meses_bons = MesesField(label='Meses de boa época', help_text='Opcional.')

    class Meta:
        model = Secao
        fields = '__all__'
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 5}),
            'nota': forms.Textarea(attrs={'rows': 2}),
            'dicas': forms.Textarea(attrs={'rows': 4}),
        }


class SecaoInline(admin.StackedInline):
    model = Secao
    form = SecaoForm
    extra = 0
    fields = ['ordem', 'titulo', 'icone', 'texto', 'foto', 'nota', 'dicas',
              'melhores_meses', 'meses_bons', 'mostrar_atracoes']
    verbose_name = 'seção'
    verbose_name_plural = 'Seções do artigo (cada uma vira um atalho no topo do artigo)'


class AtracaoInline(admin.TabularInline):
    model = Atracao
    extra = 0
    fields = ['ordem', 'nome', 'descricao', 'foto']
    verbose_name = 'atração'
    verbose_name_plural = ('Atrações: grade de fotos com nome e frase. Aparece na seção marcada '
                           'com "Mostrar as atrações aqui"')


class ArtigoForm(forms.ModelForm):
    class Meta:
        model = Artigo
        fields = '__all__'
        widgets = {
            'data_publicacao': CALENDARIO,
            'introducao': forms.Textarea(attrs={'rows': 6}),
            'resumo': forms.Textarea(attrs={'rows': 2}),
        }


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    form = ArtigoForm
    list_display = ['foto', 'titulo', 'categoria', 'data', 'situacao_etiqueta', 'destaque',
                    'leituras', 'no_site']
    list_display_links = ['titulo']
    list_editable = ['destaque']
    list_filter = ['publicado', 'categoria', 'destaque']
    search_fields = ['titulo', 'resumo', 'introducao']
    date_hierarchy = 'data_publicacao'
    prepopulated_fields = {'slug': ['titulo']}
    autocomplete_fields = ['destino']
    readonly_fields = ['previa_capa', 'tempo_de_leitura', 'leituras', 'criado_em', 'atualizado_em']
    actions = ['publicar', 'voltar_para_rascunho']
    inlines = [SecaoInline, AtracaoInline]
    save_on_top = True
    list_per_page = 30

    fieldsets = [
        ('O artigo', {
            'fields': ['titulo', 'slug', 'categoria', 'resumo', 'capa', 'previa_capa', 'autor'],
        }),
        ('Publicação', {
            'fields': ['publicado', 'data_publicacao', 'destaque'],
            'description': 'Desmarcado fica como <b>rascunho</b>: só você vê, pelo botão '
                           '"Ver no site". Marcado com data de hoje ou antes: <b>no ar</b>. '
                           'Marcado com data futura: <b>agendado</b>, entra no ar sozinho no dia.',
        }),
        ('Texto de abertura', {
            'fields': ['introducao', 'tempo_de_leitura'],
        }),
        ('Cartão na página do blog', {
            'classes': ['collapse'],
            'fields': ['etiqueta', 'cor_etiqueta'],
            'description': 'A etiqueta colorida que aparece sobre a foto do cartão.',
        }),
        ('Viagem ligada', {
            'classes': ['collapse'],
            'fields': ['destino'],
        }),
        ('Registro', {
            'classes': ['collapse'],
            'fields': ['leituras', 'criado_em', 'atualizado_em'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria')

    @admin.display(description='')
    def foto(self, artigo):
        return miniatura(artigo.capa, artigo.titulo)

    @admin.display(description='Data', ordering='data_publicacao')
    def data(self, artigo):
        return formats.date_format(artigo.data_publicacao, 'd/m/Y')

    @admin.display(description='Situação', ordering='publicado')
    def situacao_etiqueta(self, artigo):
        if artigo.situacao == 'no_ar':
            return format_html('<span class="etiqueta etiqueta--publicada">no ar</span>')
        if artigo.situacao == 'agendado':
            return format_html('<span class="etiqueta etiqueta--pendente">agendado</span>')
        return format_html('<span class="etiqueta etiqueta--cancelada">rascunho</span>')

    @admin.display(description='')
    def no_site(self, artigo):
        rotulo = 'abrir' if artigo.no_ar else 'pré-visualizar'
        return format_html('<a href="{}" target="_blank" rel="noopener">{} &#8599;</a>',
                           artigo.get_absolute_url(), rotulo)

    @admin.display(description='Foto de capa como fica no site')
    def previa_capa(self, artigo):
        if not artigo.capa:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem capa: a página usa o fundo verde da Soar.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">',
                           artigo.capa.url)

    @admin.display(description='Tempo de leitura')
    def tempo_de_leitura(self, artigo):
        if not artigo.pk:
            return 'Calculado sozinho depois de salvar.'
        return '{} min (calculado sozinho pelo tamanho do texto)'.format(artigo.minutos_de_leitura)

    @admin.action(description='Publicar os artigos selecionados')
    def publicar(self, request, queryset):
        total = queryset.update(publicado=True)
        self.message_user(request, f'{total} artigo(s) publicado(s). Os que têm data futura ficam '
                                   'agendados.', messages.SUCCESS)

    @admin.action(description='Voltar para rascunho os artigos selecionados')
    def voltar_para_rascunho(self, request, queryset):
        total = queryset.update(publicado=False)
        self.message_user(request, f'{total} artigo(s) fora do ar.', messages.WARNING)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'icone', 'ordem', 'total_artigos']
    list_editable = ['ordem']
    prepopulated_fields = {'slug': ['nome']}
    fields = ['nome', 'slug', 'icone', 'ordem']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total=Count('artigos'))

    @admin.display(description='Artigos', ordering='total')
    def total_artigos(self, categoria):
        return categoria.total


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    """Quem pediu as novidades do blog. Dá para baixar a lista para o envio."""

    list_display = ['email', 'criado_em', 'origem']
    search_fields = ['email']
    date_hierarchy = 'criado_em'
    readonly_fields = ['criado_em']
    actions = ['baixar_csv']
    list_per_page = 50

    @admin.action(description='Baixar os e-mails selecionados (planilha CSV)')
    def baixar_csv(self, request, queryset):
        import csv

        from django.http import HttpResponse
        resposta = HttpResponse(content_type='text/csv; charset=utf-8')
        resposta['Content-Disposition'] = 'attachment; filename="newsletter-soar.csv"'
        resposta.write('\ufeff')
        escritor = csv.writer(resposta, delimiter=';')
        escritor.writerow(['E-mail', 'Inscrito em'])
        for inscricao in queryset:
            escritor.writerow([inscricao.email, inscricao.criado_em.strftime('%d/%m/%Y %H:%M')])
        return resposta
