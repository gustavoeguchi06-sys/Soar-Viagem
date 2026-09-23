"""Blog Soar: artigos que o dono escreve e publica pelo painel.

Um artigo é montado em blocos, do jeito que a página mostra: título e resumo,
um texto de abertura, depois seções (cada uma vira um item do "Neste artigo
você vai ver") e, se quiser, uma grade de atrações. Nada de HTML: o dono
escreve texto corrido e marca caixas, e a página cuida da aparência. Assim
não tem como uma tag mal fechada quebrar a página, nem como alguém colar
código no texto.

Quando o artigo aparece no site é decidido por duas coisas juntas:
`publicado` marcado E `data_publicacao` já chegou. Isso dá três situações,
que o painel mostra na lista:

- Rascunho: `publicado` desmarcado. Ninguém vê, só o dono (pré-visualização).
- Agendado: marcado, mas com data futura. Entra no ar sozinho no dia.
- No ar: marcado e com data de hoje ou antes.
"""
import math
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from destinations.models import Destino

# Ícones do sprite do site (templates/partials/_icones.html) que fazem sentido
# no blog. O dono escolhe pelo nome; o código do ícone não aparece para ele.
ICONES = [
    ('info', 'Informação (i)'),
    ('pin', 'Alfinete de mapa'),
    ('mapa', 'Mapa'),
    ('calendario', 'Calendário'),
    ('relogio', 'Relógio'),
    ('camera', 'Câmera'),
    ('onibus', 'Ônibus'),
    ('cama', 'Cama'),
    ('hotel', 'Hotel'),
    ('mala', 'Mala'),
    ('mochila', 'Mochila'),
    ('doc', 'Documento'),
    ('escudo', 'Escudo (segurança)'),
    ('guia', 'Guia'),
    ('grupo', 'Grupo de pessoas'),
    ('coracao', 'Coração'),
    ('estrela', 'Estrela'),
    ('ticket', 'Ingresso'),
]

CORES = [
    ('verde', 'Verde'),
    ('teal', 'Verde-água'),
    ('azul', 'Azul'),
    ('roxo', 'Roxo'),
    ('laranja', 'Laranja'),
    ('rosa', 'Rosa'),
]

MESES = [
    (1, 'Jan'), (2, 'Fev'), (3, 'Mar'), (4, 'Abr'), (5, 'Mai'), (6, 'Jun'),
    (7, 'Jul'), (8, 'Ago'), (9, 'Set'), (10, 'Out'), (11, 'Nov'), (12, 'Dez'),
]

PALAVRAS_POR_MINUTO = 200


def _paragrafos(texto):
    """Texto corrido -> lista de parágrafos (separados por linha em branco)."""
    return [p.strip() for p in re.split(r'\n\s*\n', texto or '') if p.strip()]


def _meses_de(valor):
    """"5,6,7" -> {5, 6, 7}. Aceita vazio."""
    return {int(m) for m in (valor or '').split(',') if m.strip().isdigit()}


class Categoria(models.Model):
    nome = models.CharField('Nome', max_length=60, unique=True)
    slug = models.SlugField('Endereço', max_length=70, unique=True,
                            help_text='Preenchido sozinho a partir do nome.')
    icone = models.CharField('Ícone', max_length=20, choices=ICONES, default='pin',
                             help_text='Aparece na aba da categoria, no topo do blog.')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0,
                                             help_text='Menor aparece primeiro.')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class ArtigoQuerySet(models.QuerySet):
    def no_ar(self):
        """Só o que o público pode ver: publicado e com a data já chegada."""
        return self.filter(publicado=True, data_publicacao__lte=timezone.localdate())


class Artigo(models.Model):
    titulo = models.CharField('Título', max_length=160)
    slug = models.SlugField('Endereço', max_length=170, unique=True,
                            help_text='Parte final do link do artigo. Preenchido sozinho a partir '
                                      'do título; só mude se souber o que está fazendo, porque '
                                      'links antigos param de funcionar.')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='artigos',
                                  verbose_name='Categoria')
    resumo = models.CharField('Resumo', max_length=240,
                              help_text='Uma ou duas frases. Aparece no cartão do blog e embaixo '
                                        'do título do artigo.')
    capa = models.ImageField('Foto de capa', upload_to='blog/capas/', blank=True, null=True,
                             help_text='Foto larga (deitada). Sem foto, a página usa o fundo '
                                       'verde da Soar.')
    autor = models.CharField('Autor', max_length=80, default='Equipe Soar')

    publicado = models.BooleanField(
        'Publicado', default=False,
        help_text='Desmarcado = rascunho: só você vê. Marcado = vai ao ar na data de publicação.')
    data_publicacao = models.DateField(
        'Data de publicação', default=timezone.localdate,
        help_text='Escolha no calendário. Com data futura, o artigo fica agendado e entra no ar '
                  'sozinho nesse dia.')
    destaque = models.BooleanField('Destaque', default=False,
                                   help_text='O artigo em destaque mais recente abre o blog em '
                                             'tamanho grande.')

    etiqueta = models.CharField('Etiqueta do cartão', max_length=40, blank=True,
                                help_text='Palavra curta sobre a foto do cartão, ex.: "Jalapão". '
                                          'Em branco, usa o nome da categoria.')
    cor_etiqueta = models.CharField('Cor da etiqueta', max_length=10, choices=CORES,
                                    default='verde')

    introducao = models.TextField(
        'Texto de abertura', blank=True,
        help_text='Vem antes das seções. Para começar um parágrafo novo, deixe uma linha em branco.')
    destino = models.ForeignKey(
        Destino, on_delete=models.SET_NULL, null=True, blank=True, related_name='artigos',
        verbose_name='Viagem ligada ao artigo',
        help_text='Opcional. O final do artigo ganha um botão para a página dessa viagem.')

    leituras = models.PositiveIntegerField('Leituras', default=0, editable=False)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    objects = ArtigoQuerySet.as_manager()

    class Meta:
        verbose_name = 'Artigo'
        verbose_name_plural = 'Artigos'
        ordering = ['-data_publicacao', '-id']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:170]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:artigo', kwargs={'slug': self.slug})

    @property
    def situacao(self):
        """'rascunho', 'agendado' ou 'no_ar' — o que o painel mostra na lista."""
        if not self.publicado:
            return 'rascunho'
        if self.data_publicacao and self.data_publicacao > timezone.localdate():
            return 'agendado'
        return 'no_ar'

    @property
    def no_ar(self):
        return self.situacao == 'no_ar'

    @property
    def etiqueta_exibida(self):
        return self.etiqueta or self.categoria.nome

    @property
    def paragrafos(self):
        return _paragrafos(self.introducao)

    @property
    def minutos_de_leitura(self):
        """Calculado do texto, para ninguém precisar contar nem esquecer de atualizar."""
        textos = [self.introducao]
        for s in self.secoes.all():
            textos += [s.titulo, s.texto, s.nota, s.dicas]
        palavras = sum(len((t or '').split()) for t in textos)
        return max(1, math.ceil(palavras / PALAVRAS_POR_MINUTO))


class Secao(models.Model):
    artigo = models.ForeignKey(Artigo, on_delete=models.CASCADE, related_name='secoes')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    titulo = models.CharField('Título da seção', max_length=120,
                              help_text='Vira também um atalho no quadro "Neste artigo você vai ver".')
    icone = models.CharField('Ícone do atalho', max_length=20, choices=ICONES, default='info')
    texto = models.TextField('Texto', blank=True,
                             help_text='Para começar um parágrafo novo, deixe uma linha em branco.')
    foto = models.ImageField('Foto', upload_to='blog/secoes/', blank=True, null=True,
                             help_text='Opcional. Aparece depois do texto.')
    nota = models.TextField('Caixa de destaque', blank=True,
                            help_text='Opcional. Um recado em caixa verde, ex.: uma dica importante.')
    dicas = models.TextField('Lista com ✓', blank=True,
                             help_text='Opcional. Um item por linha.')
    melhores_meses = models.CharField('Meses de ótima época', max_length=40, blank=True)
    meses_bons = models.CharField('Meses de boa época', max_length=40, blank=True)
    mostrar_atracoes = models.BooleanField(
        'Mostrar as atrações aqui', default=False,
        help_text='Coloca nesta seção a grade de atrações cadastrada no fim do artigo.')

    class Meta:
        verbose_name = 'Seção'
        verbose_name_plural = 'Seções do artigo'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo

    @property
    def ancora(self):
        return slugify(self.titulo)[:60] or 'secao-{}'.format(self.pk)

    @property
    def paragrafos(self):
        return _paragrafos(self.texto)

    @property
    def lista_dicas(self):
        return [linha.strip() for linha in (self.dicas or '').splitlines() if linha.strip()]

    @property
    def tem_meses(self):
        return bool(self.melhores_meses or self.meses_bons)

    @property
    def calendario(self):
        """Os 12 meses com a classe de cada um, na ordem do ano."""
        otimos, bons = _meses_de(self.melhores_meses), _meses_de(self.meses_bons)
        return [{'sigla': sigla.upper(),
                 'classe': 'otima' if n in otimos else ('boa' if n in bons else '')}
                for n, sigla in MESES]

    @property
    def tem_meses_bons(self):
        return bool(_meses_de(self.meses_bons) - _meses_de(self.melhores_meses))


class Atracao(models.Model):
    artigo = models.ForeignKey(Artigo, on_delete=models.CASCADE, related_name='atracoes')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    nome = models.CharField('Nome', max_length=80)
    descricao = models.CharField('Frase curta', max_length=140, blank=True)
    foto = models.ImageField('Foto', upload_to='blog/atracoes/', blank=True, null=True)

    class Meta:
        verbose_name = 'Atração'
        verbose_name_plural = 'Atrações (grade de fotos)'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.nome
