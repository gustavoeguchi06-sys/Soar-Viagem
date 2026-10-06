"""Cadastro de destinos e hospedagens no painel do dono.

Duas decisões guiam este arquivo:

**Preço se edita na lista.** Corrigir o preço de seis destinos abrindo seis
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
                     DiferencialSobre, FotoSobre, ImagemHospedagem, Interessado, ItemSoar60,
                     NumeroSobre, PaginaSobre, PaginaSoar60, PassoSoar60, PerguntaFrequente,
                     PerguntaSoar60, PrecoQuarto, Saida, ServicoViagem,
                     SlideInicio, TextoBanner, VideoDestino, VideoSoar60)

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


def previa_video(arquivo):
    """O vídeo enviado, pequeno e com os controles, para conferir antes de salvar de novo."""
    if not arquivo:
        return format_html('<span class="miniatura miniatura--vazia">sem vídeo</span>')
    return format_html('<video class="miniatura miniatura--video" src="{}" controls '
                       'preload="metadata"></video>', arquivo.url)


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


class VideoDestinoInline(admin.TabularInline):
    model = VideoDestino
    extra = 0
    fields = ['arquivo', 'previa', 'capa', 'legenda', 'ordem']
    readonly_fields = ['previa']
    verbose_name = 'vídeo'
    verbose_name_plural = 'Vídeos da galeria'

    @admin.display(description='Prévia')
    def previa(self, obj):
        return previa_video(obj.arquivo)


class DestaqueViagemInline(admin.TabularInline):
    model = DestaqueViagem
    extra = 0
    fields = ['ordem', 'texto']
    verbose_name = 'destaque'
    verbose_name_plural = 'Destaques da viagem (o que a pessoa vai conhecer)'


class DiaRoteiroInline(admin.StackedInline):
    model = DiaRoteiro
    extra = 0
    fields = ['ordem', 'titulo', 'resumo', 'detalhe']
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
    # o bloco "Incluso e não incluso" aparece logo antes deste, depois do roteiro
    # (templates/admin/destinations/destino/change_form.html)
    incluso_antes = True


class HospedagemInline(admin.StackedInline):
    """A hospedagem é parte do pacote: cadastra-se dentro do destino.

    A Soar não vende hospedagem avulsa, então ela não tem tela própria no
    painel. Nome e foto principal ficam aqui; as fotos extras (os
    quartos) abrem pelo botão "Adicionar ou ver as fotos da hospedagem".
    """

    model = Hospedagem
    extra = 0
    fields = ['nome', 'imagem', 'previa', 'mais_fotos']
    readonly_fields = ['previa', 'mais_fotos']
    show_change_link = True
    verbose_name = 'hospedagem'
    verbose_name_plural = 'Hospedagem do pacote'

    @admin.display(description='Foto como fica no site')
    def previa(self, hospedagem):
        return miniatura(hospedagem.imagem, hospedagem.nome)

    @admin.display(description='Mais fotos (quartos, piscina...)')
    def mais_fotos(self, hospedagem):
        # As fotos extras têm tela própria (a hospedagem já precisa existir):
        # o botão fica à vista aqui, no lugar do lápis pequeno do Django.
        from django.urls import reverse
        if not hospedagem.pk:
            return 'Salve o destino primeiro; depois aparece aqui o botão para mais fotos.'
        total = hospedagem.imagens.count()
        return format_html(
            '<a class="button" href="{}">Adicionar ou ver as fotos da hospedagem</a> '
            '<span class="help">{} foto{} além da principal</span>',
            reverse('admin:destinations_hospedagem_change', args=[hospedagem.pk]),
            total, '' if total == 1 else 's')


# --------------------------------------------------------------------------- #
# Destino
# --------------------------------------------------------------------------- #

class SaidaInline(admin.TabularInline):
    """As datas de saída do destino, uma por linha, com calendário e os quartos de cada tipo."""

    model = Saida
    extra = 1
    fields = ['data_ida', 'data_volta', 'vagas', 'quartos_single', 'quartos_casal',
              'quartos_duplo', 'quartos_triplo']
    formfield_overrides = {
        models.DateField: {'widget': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')},
        models.PositiveSmallIntegerField: {
            'widget': forms.NumberInput(attrs={'min': 0, 'class': 'campo-curto'})},
    }
    verbose_name = 'saída'
    verbose_name_plural = ('Datas de saída: as que já passaram somem sozinhas. Em "Quartos", '
                           'quantos quartos de cada tipo ainda há na data (em branco, o tipo não '
                           'aparece; 0, aparece como esgotado)')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for campo in ('data_ida', 'data_volta'):
            formset.form.base_fields[campo].input_formats = ['%Y-%m-%d']
        return formset


class PrecoQuartoInline(admin.TabularInline):
    """O preço por pessoa de cada tipo de quarto: cada um com o seu valor."""

    model = PrecoQuarto
    fields = ['tipo', 'preco']
    formfield_overrides = {**PRECO_BRL}
    verbose_name = 'preço'
    verbose_name_plural = ('Preços por quarto (valor por pessoa; só aparecem no site os tipos '
                           'cadastrados aqui)')

    def get_extra(self, request, obj=None, **kwargs):
        # destino novo ou ainda sem preço: já abre com linhas para preencher
        return 0 if obj is not None and obj.precos.exists() else 4


class SeletorDeIcone(forms.RadioSelect):
    """A lista de ícones como botões com o desenho, em vez de uma lista de nomes."""

    def render(self, name, value, attrs=None, renderer=None):
        opcoes = []
        for valor, rotulo in self.choices:
            if not valor:
                continue
            id_op = '{}_{}'.format((attrs or {}).get('id', name), valor)
            opcoes.append(format_html(
                '<label class="seletor-icone__op" for="{}" title="{}">'
                '<input type="radio" name="{}" value="{}" id="{}"{}>'
                '<svg class="ic" aria-hidden="true"><use href="#{}"></use></svg>'
                '<span>{}</span></label>',
                id_op, rotulo, name, valor, id_op,
                format_html(' checked') if str(value) == str(valor) else '',
                valor, rotulo))
        return format_html('<div class="seletor-icone">{}</div>',
                           format_html(''.join(['{}'] * len(opcoes)), *opcoes))


class ServicoViagemInline(admin.StackedInline):
    """A faixa de ícones da página da viagem (Transporte confortável, Guias...)."""

    model = ServicoViagem
    extra = 0
    fields = ['icone', ('titulo', 'sub'), 'ordem']
    formfield_overrides = {}
    verbose_name = 'serviço'
    verbose_name_plural = ('Faixa de serviços da página (ícone e duas linhas de texto; sem nenhum '
                           'cadastrado, a página usa a faixa padrão da Soar)')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'icone':
            kwargs['widget'] = SeletorDeIcone
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ['capa', 'nome', 'regiao', 'a_partir_de',
                    'saidas_no_site', 'destaque', 'soar_60', 'situacao', 'no_site']
    list_display_links = ['nome']
    list_editable = ['destaque', 'soar_60']
    list_filter = ['destaque', 'soar_60', 'regiao']
    search_fields = ['nome', 'regiao', 'descricao']
    prepopulated_fields = {'slug': ['nome']}
    formfield_overrides = {**TEXTO_CURTO, **PRECO_BRL}
    save_on_top = True
    list_per_page = 30
    readonly_fields = ['previa_capa', 'criado_em', 'a_partir_de']
    inlines = [PrecoQuartoInline, SaidaInline, ServicoViagemInline, HospedagemInline, ImagemDestinoInline, VideoDestinoInline,
               DestaqueViagemInline, DiaRoteiroInline, PerguntaFrequenteInline]

    fieldsets = [
        ('O destino no catálogo', {
            'fields': ['nome', 'slug', 'regiao', 'descricao',
                       'imagem_capa', 'previa_capa', 'melhor_epoca', 'destaque', 'soar_60'],
            'description': 'O mínimo para o destino existir. A operadora só trabalha '
                           'no Brasil, então o país é sempre Brasil. O resto da página '
                           'tem texto padrão e pode ficar para depois.',
        }),
        ('Preços', {
            'fields': ['a_partir_de'],
            'description': 'Os preços ficam no bloco <b>Preços por quarto</b>, mais abaixo: um '
                           'valor por pessoa para cada tipo de quarto. O "a partir de" do site é '
                           'o menor deles e se atualiza sozinho ao salvar.',
        }),
        ('Capa da página de viagem', {
            'classes': ['collapse'],
            'fields': ['selo', 'subtitulo', 'estado'],
            'description': 'Tudo opcional. Em branco, a página usa o texto padrão da Soar.',
        }),
        # Mostrado entre o roteiro e as perguntas frequentes, e não aqui em cima
        # (templates/admin/destinations/destino/change_form.html).
        ('Incluso e não incluso', {
            'classes': ['collapse', 'bloco-incluso'],
            'fields': ['incluso', 'nao_incluso'],
            'description': 'Cada um vira um bloco separado na página da viagem. Escreva um '
                           'item por linha; linha que termina com ":" vira título dos tópicos '
                           'de baixo (ex.: Passeios:). "Não incluso" em branco: o bloco não '
                           'aparece.',
        }),
        ('Textos da página', {
            'classes': ['collapse'],
            'fields': ['hospedagem_sub', 'informacoes'],
            'description': 'Em "informações", escreva um item por linha.',
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

    @admin.display(description='A partir de', ordering='preco_base')
    def a_partir_de(self, destino):
        if destino.preco_base is None:
            return 'sob consulta'
        inteiro, centavos = f'{destino.preco_base:,.2f}'.split('.')
        return 'R$ {},{} por pessoa'.format(inteiro.replace(',', '.'), centavos)

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
        if destino.preco_base:
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
    """Tela de uma hospedagem, só para as fotos extras dos quartos.

    Não aparece no menu do painel (a hospedagem se cadastra dentro do
    destino); abre pelo botão "Adicionar ou ver as fotos da hospedagem" na
    tela do destino.
    """

    list_display = ['foto', 'nome', 'destino']
    list_display_links = ['nome']
    list_filter = ['destino']
    search_fields = ['nome', 'destino__nome']
    autocomplete_fields = ['destino']
    formfield_overrides = {**TEXTO_CURTO, **PRECO_BRL}
    save_on_top = True
    list_per_page = 30
    readonly_fields = ['previa_imagem']
    inlines = [ImagemHospedagemInline]

    fieldsets = [
        ('A hospedagem', {
            'fields': ['destino', 'nome'],
        }),
        ('Foto', {
            'fields': ['imagem', 'previa_imagem'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('destino')

    def has_module_permission(self, request):
        return False

    def response_change(self, request, obj):
        """Salvou as fotos: volta para o destino, onde a hospedagem mora."""
        if '_continue' not in request.POST and '_addanother' not in request.POST:
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            self.message_user(request, 'Fotos da hospedagem salvas.')
            return HttpResponseRedirect(reverse('admin:destinations_destino_change',
                                                args=[obj.destino_id]))
        return super().response_change(request, obj)

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

@admin.register(TextoBanner)
class TextoBannerAdmin(admin.ModelAdmin):
    """Título e frase do banner. Só existe um, então a tela abre direto nele."""

    fields = ['titulo', 'subtitulo', 'fotos_do_banner']
    readonly_fields = ['fotos_do_banner']

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:destinations_textobanner_change',
                                args=[TextoBanner.para_editar().pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def response_change(self, request, obj):
        # depois de salvar, volta para as fotos do banner, que é onde a aba fica
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        if '_continue' in request.POST:
            return super().response_change(request, obj)
        messages.success(request, 'Texto do banner salvo.')
        return redirect(reverse('admin:destinations_slideinicio_changelist'))

    @admin.display(description='Fotos e vídeos')
    def fotos_do_banner(self, texto):
        from django.urls import reverse
        return format_html('<a href="{}">Fotos e vídeos que giram no banner ({} no ar) &rarr;</a>',
                           reverse('admin:destinations_slideinicio_changelist'),
                           SlideInicio.objects.filter(ativo=True).count())


@admin.register(SlideInicio)
class SlideInicioAdmin(admin.ModelAdmin):
    """As fotos (e vídeos) que giram no topo da página inicial."""

    # o quadro "Texto do banner" no topo da lista
    change_list_template = 'admin/destinations/slideinicio/change_list.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), 'texto_banner': TextoBanner.para_editar()}
        return super().changelist_view(request, extra_context)

    list_display = ['foto', 'legenda', 'tem_video', 'ordem', 'ativo']
    list_display_links = ['foto', 'legenda']
    list_editable = ['ordem', 'ativo']
    fields = ['imagem', 'previa', 'legenda', 'video', 'previa_do_video', 'ordem', 'ativo']
    readonly_fields = ['previa', 'previa_do_video']

    @admin.display(description='Vídeo', boolean=True)
    def tem_video(self, slide):
        return bool(slide.video)

    @admin.display(description='Vídeo enviado')
    def previa_do_video(self, slide):
        return previa_video(slide.video)

    @admin.display(description='')
    def foto(self, slide):
        return miniatura(slide.imagem, slide.legenda)

    @admin.display(description='Como fica')
    def previa(self, slide):
        if not slide.imagem:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto: a página usa as fotos de exemplo do site.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">', slide.imagem.url)


@admin.register(Interessado)
class InteressadoAdmin(admin.ModelAdmin):
    """Quem pediu "Saiba mais" numa viagem.

    Pessoa física só o dono vê (superusuário), e é ele quem escolhe para quais
    agências mandar cada uma. Outro usuário da equipe não enxerga esta lista.
    """
    list_display = ['nome', 'destino', 'whatsapp_link', 'email', 'cep', 'enviado_para',
                    'criado_em']
    list_filter = ['destino', ('agencias', admin.EmptyFieldListFilter), 'agencias']
    search_fields = ['nome', 'email', 'whatsapp', 'cep']
    date_hierarchy = 'criado_em'
    readonly_fields = ['destino', 'nome', 'email', 'whatsapp', 'cep', 'criado_em']
    fields = ['destino', 'nome', 'email', 'whatsapp', 'cep', 'criado_em', 'agencias']
    list_per_page = 30

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('destino').prefetch_related(
            'agencias')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'agencias':
            from contas.models import PerfilAgente
            kwargs['queryset'] = PerfilAgente.objects.filter(aprovado=True).order_by(
                'razao_social')
            kwargs['widget'] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # só o dono
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        # o pedido chega só pelo site
        return False

    @admin.display(description='Enviado para')
    def enviado_para(self, interessado):
        nomes = [a.razao_social for a in interessado.agencias.all()]
        return ', '.join(nomes) if nomes else format_html(
            '<span class="etiqueta etiqueta--fila">ainda não enviado</span>')

    @admin.display(description='WhatsApp', ordering='whatsapp')
    def whatsapp_link(self, interessado):
        numeros = ''.join(c for c in interessado.whatsapp if c.isdigit())
        return format_html('<a href="https://wa.me/55{}" target="_blank" rel="noopener">{}</a>',
                           numeros, interessado.whatsapp)


@admin.register(VideoSoar60)
class VideoSoar60Admin(admin.ModelAdmin):
    """Os vídeos da página do Soar 60+ (/soar-60/)."""

    # o caminho de volta para a página Soar 60+ no topo da lista
    change_list_template = 'admin/destinations/videosoar60/change_list.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), 'pagina_60': PaginaSoar60.atual()}
        return super().changelist_view(request, extra_context)

    list_display = ['titulo', 'ordem', 'ativo']
    list_editable = ['ordem', 'ativo']
    fields = ['titulo', 'arquivo', 'previa', 'capa', 'ordem', 'ativo']
    readonly_fields = ['previa']

    @admin.display(description='Vídeo enviado')
    def previa(self, video):
        return previa_video(video.arquivo)


# --------------------------------------------------------------------------- #
# Página Soar 60+: uma só, o painel abre direto no formulário dela
# --------------------------------------------------------------------------- #

class ItemSoar60Inline(admin.StackedInline):
    model = ItemSoar60
    extra = 0
    fields = ['icone', 'titulo', 'texto', 'ordem']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'icone':
            kwargs['widget'] = SeletorDeIcone
        if db_field.name == 'texto':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 2})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class PassoSoar60Inline(admin.StackedInline):
    model = PassoSoar60
    extra = 0
    fields = ['titulo', 'texto', 'ordem']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'texto':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 2})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class PerguntaSoar60Inline(admin.StackedInline):
    model = PerguntaSoar60
    extra = 0
    fields = ['pergunta', 'resposta', 'ordem']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'resposta':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 3})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(PaginaSoar60)
class PaginaSoar60Admin(admin.ModelAdmin):
    """A página /soar-60/. Só existe uma, então não tem lista: a aba abre nela."""

    inlines = [ItemSoar60Inline, PassoSoar60Inline, PerguntaSoar60Inline]
    readonly_fields = ['ver_no_site', 'previa_foto', 'videos']
    save_on_top = True
    fieldsets = [
        ('Capa', {'fields': ['ver_no_site', 'titulo', 'subtitulo', 'foto', 'previa_foto',
                             'texto_home']}),
        ('O que muda numa viagem 60+', {
            'fields': ['diferenciais_titulo', 'diferenciais_intro'],
            'description': 'Os cartões ficam no bloco "Cartões de O que muda", mais abaixo.'}),
        ('Viagens e vídeos', {
            'fields': ['viagens_titulo', 'videos_titulo', 'videos'],
            'description': 'As viagens que aparecem são as marcadas como "Soar 60+" em cada '
                           'destino. Sem nenhuma marcada, aparece o catálogo inteiro.'}),
        ('Como funciona', {'fields': ['passos_titulo'],
                           'description': 'Os passos ficam no bloco "Passos", mais abaixo.'}),
        ('Perguntas', {'fields': ['perguntas_titulo'],
                       'description': 'As perguntas ficam no bloco "Perguntas", no fim.'}),
    ]

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:destinations_paginasoar60_change',
                                args=[PaginaSoar60.atual().pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='No site')
    def ver_no_site(self, pagina):
        from django.urls import reverse
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir a página Soar 60+ '
                           '&#8599;</a>', reverse('destinations:soar_60'))

    @admin.display(description='Como fica a foto')
    def previa_foto(self, pagina):
        if not pagina.foto:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto: o site usa a ilustração das montanhas.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">',
                           pagina.foto.url)

    @admin.display(description='Vídeos')
    def videos(self, pagina):
        from django.urls import reverse
        return format_html('<a href="{}">Vídeos da página ({} no ar) &rarr;</a>',
                           reverse('admin:destinations_videosoar60_changelist'),
                           VideoSoar60.objects.filter(ativo=True).count())


# --------------------------------------------------------------------------- #
# Página "Sobre a Soar": uma só, o painel abre direto no formulário dela
# --------------------------------------------------------------------------- #

class DiferencialSobreInline(admin.StackedInline):
    model = DiferencialSobre
    extra = 0
    fields = ['icone', 'titulo', 'texto', 'ordem']
    verbose_name_plural = 'Diferenciais (cartões com ícone)'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'icone':
            kwargs['widget'] = SeletorDeIcone
        if db_field.name == 'texto':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 2})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class NumeroSobreInline(admin.TabularInline):
    model = NumeroSobre
    extra = 0
    fields = ['valor', 'legenda', 'ordem']


class FotoSobreInline(admin.TabularInline):
    model = FotoSobre
    extra = 0
    fields = ['imagem', 'previa', 'legenda', 'ordem']
    readonly_fields = ['previa']

    @admin.display(description='Prévia')
    def previa(self, obj):
        return miniatura(obj.imagem, obj.legenda)


@admin.register(PaginaSobre)
class PaginaSobreAdmin(admin.ModelAdmin):
    """A página /sobre/. Só existe uma, então não tem lista: a aba abre nela."""

    inlines = [DiferencialSobreInline, NumeroSobreInline, FotoSobreInline]
    readonly_fields = ['ver_no_site', 'previa_capa', 'previa_video']
    save_on_top = True
    fieldsets = [
        ('Capa', {'fields': ['ver_no_site', 'titulo', 'subtitulo', 'capa', 'previa_capa',
                             'video_capa', 'previa_video']}),
        ('Texto principal', {'fields': ['historia_titulo', 'historia', 'historia_foto']}),
        ('Diferenciais', {'fields': ['diferenciais_titulo'],
                          'description': 'Os cartões ficam no bloco "Diferenciais", mais abaixo.'}),
    ]

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:destinations_paginasobre_change',
                                args=[PaginaSobre.atual().pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='No site')
    def ver_no_site(self, pagina):
        from django.urls import reverse
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir a página Sobre a '
                           'Soar &#8599;</a>', reverse('destinations:sobre'))

    @admin.display(description='Como fica a foto')
    def previa_capa(self, pagina):
        if not pagina.capa:
            return format_html('<span class="miniatura miniatura--grande miniatura--vazia">'
                               'Sem foto: a página usa uma ilustração da Soar.</span>')
        return format_html('<img class="miniatura miniatura--grande" src="{}" alt="">',
                           pagina.capa.url)

    @admin.display(description='Vídeo enviado')
    def previa_video(self, pagina):
        return previa_video(pagina.video_capa)
