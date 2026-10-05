import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

from soar.videos import ajuda as ajuda_video, validar_foto, validar_video

from .quartos import ESCOLHAS as TIPOS_DE_QUARTO, ICONES, ORDEM as ORDEM_DOS_QUARTOS, POR_CHAVE


MESES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}


def textos_do_periodo(ida, volta):
    """Os textos que a página mostra para uma viagem de `ida` a `volta`.

    Devolve período, mês e ano, duração e a frase completa da saída
    (ex.: "16 a 21 de Junho de 2027"). Sem as duas datas, devolve None.
    """
    if not (ida and volta):
        return None
    if volta < ida:
        ida, volta = volta, ida

    total_dias = (volta - ida).days + 1
    noites = max(total_dias - 1, 0)
    mes_ida = MESES[ida.month]
    textos = {
        'dias': f'{total_dias} dia' + ('' if total_dias == 1 else 's'),
        'noites': f'{noites} noite' + ('' if noites == 1 else 's'),
        'mes_ano': f'{mes_ida} {ida.year}',
    }
    if (ida.month, ida.year) == (volta.month, volta.year):
        textos['periodo'] = f'{ida.day} a {volta.day}'
        textos['proxima_saida'] = f'{ida.day} a {volta.day} de {mes_ida} de {ida.year}'
    elif ida.year == volta.year:
        mes_volta = MESES[volta.month]
        textos['periodo'] = f'{ida.day} de {mes_ida} a {volta.day} de {mes_volta}'
        textos['proxima_saida'] = (f'{ida.day} de {mes_ida} a {volta.day} '
                                   f'de {mes_volta} de {ida.year}')
    else:
        mes_volta = MESES[volta.month]
        textos['periodo'] = (f'{ida.day} de {mes_ida} de {ida.year} a '
                             f'{volta.day} de {mes_volta} de {volta.year}')
        textos['proxima_saida'] = textos['periodo']
    return textos


class Destino(models.Model):
    REGIOES = [
        ('Norte', 'Norte'),
        ('Nordeste', 'Nordeste'),
        ('Centro-Oeste', 'Centro-Oeste'),
        ('Sudeste', 'Sudeste'),
        ('Sul', 'Sul'),
    ]

    nome = models.CharField('Nome', max_length=120)
    slug = models.SlugField('Slug', max_length=140, unique=True, blank=True,
                            help_text='Preenchido automaticamente a partir do nome.')
    pais = models.CharField('País', max_length=80, default='Brasil')
    descricao = models.TextField('Descrição')
    imagem_capa = models.ImageField(validators=[validar_foto], verbose_name='Imagem de capa', upload_to='destinos/', blank=True, null=True)
    melhor_epoca = models.CharField('Melhor época para visitar', max_length=120, blank=True)
    destaque = models.BooleanField('Destaque na página inicial', default=False)
    soar_60 = models.BooleanField(
        'Faz parte do Soar 60+', default=False,
        help_text='Marque as viagens de ritmo mais tranquilo, que aparecem na '
                  'página do Soar 60+. Se nenhuma estiver marcada, a página '
                  'mostra o catálogo inteiro.')
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    # ----------------------------------------------------------------- #
    # Sobre a viagem — o que a página do destino mostra além do catálogo.
    # Tudo opcional: em branco, a página usa o texto padrão da operadora
    # (destinations/conteudo.py), então um destino novo já nasce completo e o
    # dono vai preenchendo o que quiser mudar.
    # ----------------------------------------------------------------- #
    selo = models.CharField('Selo', max_length=40, blank=True,
                            help_text='Aparece sobre o título. Ex.: Expedição.')
    subtitulo = models.CharField('Subtítulo', max_length=160, blank=True,
                                 help_text='A frase logo abaixo do nome, na capa.')
    regiao = models.CharField('Região', max_length=20, blank=True, choices=REGIOES,
                              help_text='Região do Brasil onde fica o destino.')
    estado = models.CharField('Estado', max_length=60, blank=True,
                              help_text='Ex.: Tocantins. Sem isso, mostra o país.')
    data_ida = models.DateField('Data de ida', blank=True, null=True,
                                help_text='Escolha no calendário o dia de saída.')
    data_volta = models.DateField('Data de volta', blank=True, null=True,
                                  help_text='O dia do retorno. Período, mês, duração e '
                                            'próxima saída são preenchidos a partir das datas.')
    periodo = models.CharField('Período', max_length=40, blank=True,
                               help_text='Preenchido a partir das datas de ida e volta.')
    mes_ano = models.CharField('Mês e ano', max_length=40, blank=True,
                               help_text='Ex.: Junho 2027.')
    dias = models.CharField('Duração em dias', max_length=20, blank=True,
                            help_text='Ex.: 6 dias.')
    noites = models.CharField('Duração em noites', max_length=20, blank=True,
                              help_text='Ex.: 5 noites.')
    proxima_saida = models.CharField('Próxima saída', max_length=120, blank=True,
                                     help_text='Ex.: 16 a 21 de Junho de 2027.')
    vagas = models.PositiveSmallIntegerField('Vagas disponíveis', blank=True, null=True)
    # O "a partir de": o menor preço por pessoa entre os quartos (PrecoQuarto).
    # Atualizado sozinho quando o dono mexe nos preços; não é digitado.
    preco_base = models.DecimalField('A partir de (R$ por pessoa)', max_digits=9,
                                     decimal_places=2, blank=True, null=True,
                                     help_text='O menor preço por pessoa entre os quartos. Sem '
                                               'preço, a página mostra "sob consulta".')
    hospedagem_sub = models.CharField('Chamada da hospedagem', max_length=120, blank=True,
                                      help_text='Ex.: A duas quadras da Ilha do Amor.')
    incluso = models.TextField('O que está incluso', blank=True,
                               help_text='Um item por linha. Linha que termina com ":" vira título, e as linhas de baixo ficam como tópicos dele (ex.: Passeios:). Não precisa pôr - ou • no começo.')
    nao_incluso = models.TextField('O que não está incluso', blank=True,
                                   help_text='Um item por linha. Linha que termina com ":" vira título, e as linhas de baixo ficam como tópicos dele (ex.: Passeios:). Não precisa pôr - ou • no começo. Em branco, a página só mostra o que está '
                                             'incluso.')
    informacoes = models.TextField('Informações importantes', blank=True,
                                   help_text='Um item por linha. Linha que termina com ":" vira título, e as linhas de baixo ficam como tópicos dele (ex.: Passeios:). Não precisa pôr - ou • no começo.')

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['-destaque', 'nome']
        indexes = [
            # A busca filtra por estes tres campos; sem indice, cada consulta
            # e uma varredura da tabela inteira.
            models.Index(fields=['nome'], name='destino_nome_idx'),
            models.Index(fields=['pais'], name='destino_pais_idx'),
        ]

    def __str__(self):
        return f'{self.nome}, {self.pais}'

    MESES = MESES

    def _preencher_datas(self):
        """Preenche período, mês, duração e próxima saída a partir das datas.

        O dono escolhe ida e volta no calendário; os textos que a página mostra
        saem daqui, sempre coerentes com as datas escolhidas.
        """
        textos = textos_do_periodo(self.data_ida, self.data_volta)
        if textos:
            for campo, valor in textos.items():
                setattr(self, campo, valor)

    @property
    def capa_card(self):
        """Imagem do cartão do catálogo: a capa, a primeira foto da galeria ou,
        sem nenhuma, a mesma ilustração que abre a página da viagem."""
        if self.imagem_capa:
            return self.imagem_capa.url
        # .all() e não .exclude(): aproveita o prefetch_related das listas
        foto = next((i for i in self.imagens.all() if i.imagem), None) if self.pk else None
        if foto:
            return foto.imagem.url
        from django.templatetags.static import static

        from .conteudo import FOTOS_PADRAO, POR_DESTINO
        fotos = POR_DESTINO.get(self.slug, {}).get('fotos') or FOTOS_PADRAO
        return static(fotos[0])

    @property
    def saidas_futuras(self):
        """Saídas que ainda não aconteceram, da mais próxima para a mais distante."""
        return self.saidas.filter(data_ida__gte=timezone.localdate()).order_by('data_ida')

    def save(self, *args, **kwargs):
        if not self.pais:
            self.pais = 'Brasil'
        if not self.slug:
            self.slug = slugify(f'{self.nome}-{self.pais}')
        self._preencher_datas()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('destinations:detalhe', kwargs={'slug': self.slug})

    def linhas(self, campo):
        """Campo de texto escrito um item por linha vira lista (vazias fora)."""
        return [linha.strip() for linha in getattr(self, campo).splitlines() if linha.strip()]

    @property
    def media_avaliacoes(self):
        """Media das avaliacoes ja aprovadas.

        So conta as publicadas: enquanto uma avaliacao esta na fila de
        moderacao ela nao pode mexer na nota que aparece na vitrine.
        """
        # .all() e não .publicadas(): aproveita o prefetch_related das listas
        notas = [a.nota for a in self.avaliacoes.all() if a.publicada]
        if not notas:
            return None
        return round(sum(notas) / len(notas), 1)


class ImagemDestino(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='imagens', verbose_name='Destino')
    imagem = models.ImageField(validators=[validar_foto], verbose_name='Imagem', upload_to='destinos/galeria/')
    legenda = models.CharField('Legenda', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Imagem do destino'
        verbose_name_plural = 'Imagens do destino'

    def __str__(self):
        return self.legenda or f'Imagem de {self.destino.nome}'


class VideoDestino(models.Model):
    """Vídeo da galeria da página da viagem, ao lado das fotos."""

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='videos', verbose_name='Destino')
    arquivo = models.FileField('Vídeo', upload_to='destinos/videos/',
                               validators=[validar_video], help_text=ajuda_video())
    capa = models.ImageField(validators=[validar_foto], verbose_name='Foto de capa', upload_to='destinos/videos/capas/', blank=True,
                             null=True, help_text='Opcional. Aparece antes de o vídeo tocar.')
    legenda = models.CharField('Legenda', max_length=200, blank=True)
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Vídeo do destino'
        verbose_name_plural = 'Vídeos do destino'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.legenda or f'Vídeo de {self.destino.nome}'


class Hospedagem(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='hospedagens', verbose_name='Destino')
    nome = models.CharField('Nome', max_length=120)
    endereco = models.CharField('Endereço', max_length=200, blank=True,
                                help_text='Onde a hospedagem fica.')
    imagem = models.ImageField(validators=[validar_foto], verbose_name='Imagem principal', upload_to='hospedagens/', blank=True, null=True)
    pacote_completo = models.BooleanField('Incluso no pacote completo', default=True,
                                          help_text='A hospedagem já está inclusa no pacote da viagem.')

    class Meta:
        verbose_name = 'Hospedagem'
        verbose_name_plural = 'Hospedagens'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ImagemHospedagem(models.Model):
    hospedagem = models.ForeignKey(Hospedagem, on_delete=models.CASCADE,
                                   related_name='imagens', verbose_name='Hospedagem')
    imagem = models.ImageField(validators=[validar_foto], verbose_name='Imagem', upload_to='hospedagens/galeria/')
    legenda = models.CharField('Legenda', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Imagem da hospedagem'
        verbose_name_plural = 'Imagens da hospedagem'

    def __str__(self):
        return self.legenda or f'Imagem de {self.hospedagem.nome}'


class DestaqueViagem(models.Model):
    """Um item da lista 'Destaques da viagem' (o que a pessoa vai conhecer)."""

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='destaques_viagem', verbose_name='Destino')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    texto = models.CharField('Destaque', max_length=120,
                             help_text='Ex.: Fervedouro do Alecrim.')

    class Meta:
        verbose_name = 'Destaque da viagem'
        verbose_name_plural = 'Destaques da viagem'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.texto


class DiaRoteiro(models.Model):
    """Um dia do roteiro dia a dia."""

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='roteiro', verbose_name='Destino')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    titulo = models.CharField('Título', max_length=120,
                              help_text='Ex.: Dia 1: Chegada em Santarém.')
    resumo = models.CharField('Resumo', max_length=200,
                              help_text='A linha que aparece com o dia fechado.')
    detalhe = models.TextField('Detalhe', blank=True,
                               help_text='O texto que abre quando a pessoa clica no dia. '
                                         'Cada linha vira um tópico no site.')
    imagem = models.ImageField(validators=[validar_foto], verbose_name='Foto do dia', upload_to='roteiro/', blank=True, null=True,
                               help_text='Opcional: sem foto, usa uma da galeria do destino.')

    class Meta:
        verbose_name = 'Dia do roteiro'
        verbose_name_plural = 'Roteiro dia a dia'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo


class PerguntaFrequente(models.Model):
    """Uma pergunta do bloco de FAQ da página da viagem."""

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='perguntas', verbose_name='Destino')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    pergunta = models.CharField('Pergunta', max_length=200)
    resposta = models.TextField('Resposta')

    class Meta:
        verbose_name = 'Pergunta frequente'
        verbose_name_plural = 'Perguntas frequentes'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.pergunta


class Saida(models.Model):
    """Uma data em que o grupo sai para o destino.

    O mesmo destino costuma ter várias saídas no ano. A página da viagem lista
    todas as que ainda vão acontecer, cada uma com as suas vagas, e o cliente
    escolhe em qual quer ir. As que já passaram somem sozinhas do site.
    """

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='saidas', verbose_name='Destino')
    data_ida = models.DateField('Ida', help_text='Dia em que o grupo sai.')
    data_volta = models.DateField('Volta', help_text='Dia do retorno.')
    vagas = models.PositiveSmallIntegerField(
        'Vagas (pessoas)', blank=True, null=True,
        help_text='Em branco, o site mostra "consulte". Com 0, aparece como esgotada.')
    # Quantos quartos de cada tipo ainda há nesta data. Em branco: o tipo não
    # aparece na lista de quartos da data.
    quartos_single = models.PositiveSmallIntegerField('Quartos Single', blank=True, null=True)
    quartos_casal = models.PositiveSmallIntegerField('Quartos Casal', blank=True, null=True)
    quartos_duplo = models.PositiveSmallIntegerField('Quartos Duplo', blank=True, null=True)
    quartos_triplo = models.PositiveSmallIntegerField('Quartos Triplo', blank=True, null=True)

    class Meta:
        verbose_name = 'Saída'
        verbose_name_plural = 'Saídas'
        ordering = ['data_ida', 'id']

    def __str__(self):
        return self.texto

    def clean(self):
        if self.data_ida and self.data_volta and self.data_volta < self.data_ida:
            raise ValidationError({'data_volta': 'A volta não pode ser antes da ida.'})

    @property
    def textos(self):
        return textos_do_periodo(self.data_ida, self.data_volta) or {}

    @property
    def texto(self):
        """Ex.: 16 a 21 de Junho de 2027."""
        return self.textos.get('proxima_saida', '')

    @property
    def quartos(self):
        """[{'nome': 'Casal', 'quantidade': 4}, ...] só dos tipos preenchidos."""
        lista = []
        for chave, nome in TIPOS_DE_QUARTO:
            quantidade = getattr(self, 'quartos_' + chave)
            if quantidade is not None:
                lista.append({'chave': chave, 'nome': nome, 'quantidade': quantidade})
        return lista

    @property
    def esgotada(self):
        # Esgotada quando as vagas zeraram, ou quando todos os quartos
        # cadastrados para a data acabaram.
        quartos = self.quartos
        return self.vagas == 0 or (bool(quartos) and all(q['quantidade'] == 0 for q in quartos))


class Interessado(models.Model):
    """Quem pediu "Saiba mais" na página de uma viagem sem ter login.

    A Soar é B2B e não vende direto. Só o dono (superusuário) vê esta lista no
    painel, e ele escolhe para quais agências parceiras mandar cada pessoa; a
    agência vê só quem foi mandado para ela. Sai sozinho depois de 1 ano
    (expurgar_dados), como promete o aviso de privacidade.
    """

    destino = models.ForeignKey(Destino, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='interessados', verbose_name='Viagem')
    nome = models.CharField('Nome', max_length=120)
    email = models.EmailField('E-mail')
    whatsapp = models.CharField('WhatsApp', max_length=20)
    cep = models.CharField('CEP', max_length=9)
    agencias = models.ManyToManyField(
        'contas.PerfilAgente', blank=True, related_name='interessados',
        verbose_name='Enviar para as agências',
        help_text='Marque as agências que vão atender esta pessoa. Ela aparece no '
                  'painel de cada agência marcada.')
    criado_em = models.DateTimeField('Pedido em', auto_now_add=True)

    class Meta:
        verbose_name = 'Interessado'
        verbose_name_plural = 'Interessados ("Saiba mais" da viagem)'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome


class TextoBanner(models.Model):
    """O título e a frase grandes do banner da página inicial. Existe um só.

    Ficam por cima de todas as fotos e vídeos que giram no banner, por isso
    não moram em cada slide.
    """

    titulo = models.CharField('Título', max_length=80,
                              default='Muito além do destino, uma Experiência',
                              help_text='A frase grande, em letras brancas. Curta: até umas 8 palavras.')
    subtitulo = models.CharField(
        'Frase embaixo do título', max_length=160, blank=True,
        default='Descubra viagens em grupo para destinos que você nunca vai esquecer.',
        help_text='Uma linha que completa o título. Em branco, não aparece.')

    class Meta:
        verbose_name = 'Texto do banner'
        verbose_name_plural = 'Texto do banner'

    def __str__(self):
        return self.titulo

    @classmethod
    def atual(cls):
        """O texto em uso; sem nada salvo ainda, o padrão (sem gravar: ver a página não escreve)."""
        return cls.objects.first() or cls()

    @classmethod
    def para_editar(cls):
        """O registro que o painel edita, criado na primeira vez que o dono abre."""
        return cls.objects.first() or cls.objects.create()


class SlideInicio(models.Model):
    """Uma foto do carrossel do topo da página inicial.

    O título e os botões do topo são fixos; o que gira são as fotos. Sem
    nenhuma foto cadastrada, a página usa as fotos de exemplo do site.
    """

    imagem = models.ImageField(validators=[validar_foto], verbose_name='Foto', upload_to='inicio/',
        help_text='Foto deitada e grande (pelo menos 1600 px de largura). Ela ocupa a tela '
                  'inteira, então o assunto principal deve ficar mais para a direita: o '
                  'título aparece à esquerda.')
    legenda = models.CharField('Descrição da foto', max_length=120, blank=True,
                               help_text='Ex.: Cachoeira no Jalapão. Lida por quem usa leitor de tela.')
    # A foto continua obrigatória: é a capa enquanto o vídeo carrega, o que
    # aparece para quem pede menos movimento no celular, e é usada em outros
    # blocos da página (fundo da chamada final, #ViajantesSoar).
    video = models.FileField(
        'Vídeo (opcional)', upload_to='inicio/videos/', blank=True,
        validators=[validar_video],
        help_text=ajuda_video('Toca sem som e em repetição no lugar da foto, que vira a capa.'))
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    ativo = models.BooleanField('Aparece no site', default=True)

    class Meta:
        verbose_name = 'Foto ou vídeo do topo da página inicial'
        verbose_name_plural = 'Fotos e vídeos do topo da página inicial'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.legenda or 'Foto {}'.format(self.pk)


class VideoSoar60(models.Model):
    """Vídeo da página do Soar 60+ (/soar-60/)."""

    titulo = models.CharField('Título', max_length=120,
                              help_text='Ex.: Como é uma viagem 60+ com a Soar.')
    arquivo = models.FileField('Vídeo', upload_to='soar60/videos/',
                               validators=[validar_video], help_text=ajuda_video())
    capa = models.ImageField(validators=[validar_foto], verbose_name='Foto de capa', upload_to='soar60/capas/', blank=True, null=True,
                             help_text='Opcional. Aparece antes de o vídeo tocar.')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)
    ativo = models.BooleanField('Aparece no site', default=True)

    class Meta:
        verbose_name = 'Vídeo do Soar 60+'
        verbose_name_plural = 'Vídeos do Soar 60+'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo


class PrecoQuarto(models.Model):
    """O preço por pessoa de um tipo de quarto da viagem.

    Cada tipo tem o seu preço: não é uma conta a partir do casal. O "a partir
    de" da viagem (Destino.preco_base) é o menor deles, atualizado sozinho
    quando um preço muda (ver o sinal no fim do arquivo).
    """

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='precos', verbose_name='Destino')
    tipo = models.CharField('Quarto', max_length=12, choices=TIPOS_DE_QUARTO)
    preco = models.DecimalField('Preço por pessoa (R$)', max_digits=9, decimal_places=2)

    class Meta:
        verbose_name = 'Preço por quarto'
        verbose_name_plural = 'Preços por quarto'
        constraints = [models.UniqueConstraint(fields=['destino', 'tipo'],
                                               name='um_preco_por_tipo_de_quarto')]

    def __str__(self):
        return '{}: R$ {}'.format(self.get_tipo_display(), self.preco)

    @property
    def ordem(self):
        return ORDEM_DOS_QUARTOS.get(self.tipo, 99)

    @property
    def pessoas(self):
        return POR_CHAVE[self.tipo]['pessoas']


class ServicoViagem(models.Model):
    """Um item da faixa de serviços da página da viagem (ícone + duas linhas).

    Sem nenhum cadastrado, a página mostra a faixa padrão da Soar.
    """

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='servicos', verbose_name='Destino')
    icone = models.CharField('Ícone', max_length=30, choices=ICONES, default='ic-onibus')
    titulo = models.CharField('Primeira linha', max_length=40, help_text='Ex.: Transporte')
    sub = models.CharField('Segunda linha', max_length=40, blank=True,
                           help_text='Ex.: confortável')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Serviço da viagem'
        verbose_name_plural = 'Serviços da viagem'
        ordering = ['ordem', 'id']

    def __str__(self):
        return ' '.join(filter(None, [self.titulo, self.sub]))


def precos_a_partir_do_casal(destino, casal):
    """Para os dados de exemplo: monta a tabela de quartos a partir de um preço de casal.

    Só cria o que falta; o que o dono já cadastrou fica como está.
    """
    from decimal import Decimal

    diferencas = {'single': 1400, 'casal': 0, 'duplo': 0, 'triplo': -200}
    existentes = set(destino.precos.values_list('tipo', flat=True))
    for tipo, diferenca in diferencas.items():
        if tipo not in existentes:
            PrecoQuarto.objects.create(destino=destino, tipo=tipo,
                                       preco=Decimal(casal) + diferenca)


def _atualizar_a_partir_de(sender, instance, **kwargs):
    """Mantém o "a partir de" da viagem igual ao menor preço por pessoa."""
    destino = Destino.objects.filter(pk=instance.destino_id).first()
    if destino is None:
        return
    menor = destino.precos.aggregate(menor=models.Min('preco'))['menor']
    if destino.preco_base != menor:
        Destino.objects.filter(pk=destino.pk).update(preco_base=menor)


models.signals.post_save.connect(_atualizar_a_partir_de, sender=PrecoQuarto)
models.signals.post_delete.connect(_atualizar_a_partir_de, sender=PrecoQuarto)


class PaginaSobre(models.Model):
    """A página "Sobre a Soar" (/sobre/). Existe uma só: o painel abre direto nela."""

    titulo = models.CharField('Título da capa', max_length=80, default='Sobre a Soar')
    subtitulo = models.CharField(
        'Frase da capa', max_length=200, blank=True,
        default='Viagens em grupo pelo Brasil, para quem quer ir além do óbvio.')
    capa = models.ImageField(validators=[validar_foto], verbose_name='Foto da capa', upload_to='sobre/', blank=True, null=True,
                             help_text='Foto deitada e grande (1920 x 1080 px). Sem foto, usa '
                                       'uma ilustração da Soar.')
    video_capa = models.FileField(
        'Vídeo da capa (opcional)', upload_to='sobre/videos/', blank=True,
        validators=[validar_video],
        help_text=ajuda_video('Toca sem som e em repetição atrás do título; a foto vira a capa.'))
    historia_titulo = models.CharField('Título do texto principal', max_length=80,
                                       default='Quem somos')
    historia = models.TextField(
        'Texto principal', blank=True,
        help_text='A história da Soar. Para começar um parágrafo novo, deixe uma linha em branco.')
    historia_foto = models.ImageField(validators=[validar_foto], verbose_name='Foto ao lado do texto', upload_to='sobre/', blank=True,
                                      null=True)
    diferenciais_titulo = models.CharField('Título dos diferenciais', max_length=80,
                                           default='Por que viajar com a Soar')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Página Sobre a Soar'
        verbose_name_plural = 'Página Sobre a Soar'

    def __str__(self):
        return 'Página Sobre a Soar'

    @classmethod
    def atual(cls):
        return cls.objects.first() or cls.objects.create()

    @property
    def paragrafos(self):
        return [p.strip() for p in re.split(r'\n\s*\n', self.historia or '') if p.strip()]


class DiferencialSobre(models.Model):
    pagina = models.ForeignKey(PaginaSobre, on_delete=models.CASCADE, related_name='diferenciais')
    icone = models.CharField('Ícone', max_length=30, choices=ICONES, default='ic-check')
    titulo = models.CharField('Título', max_length=60)
    texto = models.TextField('Texto', max_length=300, blank=True)
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'diferencial'
        verbose_name_plural = 'Diferenciais'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo


class NumeroSobre(models.Model):
    pagina = models.ForeignKey(PaginaSobre, on_delete=models.CASCADE, related_name='numeros')
    valor = models.CharField('Número', max_length=20, help_text='Ex.: +2.000')
    legenda = models.CharField('Legenda', max_length=60, help_text='Ex.: viajantes levados')
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'número'
        verbose_name_plural = 'Números da Soar (opcional; sem nenhum, a faixa não aparece)'
        ordering = ['ordem', 'id']

    def __str__(self):
        return '{} {}'.format(self.valor, self.legenda)


class FotoSobre(models.Model):
    pagina = models.ForeignKey(PaginaSobre, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(validators=[validar_foto], verbose_name='Foto', upload_to='sobre/galeria/')
    legenda = models.CharField('Legenda', max_length=120, blank=True)
    ordem = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'foto'
        verbose_name_plural = 'Fotos (opcional; sem nenhuma, a galeria não aparece)'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.legenda or 'Foto {}'.format(self.pk)


class TokenInstagram(models.Model):
    """O token do Instagram em uso, depois da primeira renovação.

    O token nasce no .env (SOAR_INSTAGRAM_TOKEN), mas vence em 60 dias e cada
    renovação devolve um token novo, que precisa ficar guardado em algum lugar
    que o site consiga escrever: aqui. Fica uma linha só. Não aparece no
    painel de propósito, porque é como uma senha da conta.
    """

    token = models.TextField()
    # sha256 do token do .env de onde este veio: se alguém gerar outro token
    # no painel da Meta e trocar o .env, o novo passa na frente deste
    origem = models.CharField(max_length=64)
    renovado_em = models.DateTimeField()
    expira_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Token do Instagram'
        verbose_name_plural = 'Token do Instagram'

    def __str__(self):
        return 'Token do Instagram (renovado em {:%d/%m/%Y})'.format(self.renovado_em)
