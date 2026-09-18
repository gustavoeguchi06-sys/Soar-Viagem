from django.db import models
from django.urls import reverse
from django.utils.text import slugify


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
    imagem_capa = models.ImageField('Imagem de capa', upload_to='destinos/', blank=True, null=True)
    preco_medio_diaria = models.DecimalField('Preço médio da diária (R$)', max_digits=8,
                                             decimal_places=2, blank=True, null=True)
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
    preco_base = models.DecimalField('Preço da viagem por tipo de quarto (R$)', max_digits=9,
                                     decimal_places=2, blank=True, null=True,
                                     help_text='Valor do quarto duplo, que abre o card de reserva. '
                                               'Sem isso, calcula a partir da diária média.')
    hospedagem_sub = models.CharField('Chamada da hospedagem', max_length=120, blank=True,
                                      help_text='Ex.: A duas quadras da Ilha do Amor.')
    incluso = models.TextField('O que está incluso', blank=True,
                               help_text='Um item por linha.')
    informacoes = models.TextField('Informações importantes', blank=True,
                                   help_text='Um item por linha.')

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

    MESES = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
    }

    def _preencher_datas(self):
        """Preenche período, mês, duração e próxima saída a partir das datas.

        O dono escolhe ida e volta no calendário; os textos que a página mostra
        saem daqui, sempre coerentes com as datas escolhidas.
        """
        ida, volta = self.data_ida, self.data_volta
        if not (ida and volta):
            return
        if volta < ida:
            ida, volta = volta, ida

        total_dias = (volta - ida).days + 1
        noites = max(total_dias - 1, 0)
        self.dias = f'{total_dias} dia' + ('' if total_dias == 1 else 's')
        self.noites = f'{noites} noite' + ('' if noites == 1 else 's')

        mes_ida = self.MESES[ida.month]
        self.mes_ano = f'{mes_ida} {ida.year}'

        if (ida.month, ida.year) == (volta.month, volta.year):
            self.periodo = f'{ida.day} a {volta.day}'
            self.proxima_saida = f'{ida.day} a {volta.day} de {mes_ida} de {ida.year}'
        elif ida.year == volta.year:
            mes_volta = self.MESES[volta.month]
            self.periodo = f'{ida.day} de {mes_ida} a {volta.day} de {mes_volta}'
            self.proxima_saida = (f'{ida.day} de {mes_ida} a {volta.day} '
                                  f'de {mes_volta} de {ida.year}')
        else:
            mes_volta = self.MESES[volta.month]
            self.periodo = (f'{ida.day} de {mes_ida} de {ida.year} a '
                            f'{volta.day} de {mes_volta} de {volta.year}')
            self.proxima_saida = self.periodo

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
        notas = [a.nota for a in self.avaliacoes.publicadas()]
        if not notas:
            return None
        return round(sum(notas) / len(notas), 1)


class ImagemDestino(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='imagens', verbose_name='Destino')
    imagem = models.ImageField('Imagem', upload_to='destinos/galeria/')
    legenda = models.CharField('Legenda', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Imagem do destino'
        verbose_name_plural = 'Imagens do destino'

    def __str__(self):
        return self.legenda or f'Imagem de {self.destino.nome}'


class Hospedagem(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='hospedagens', verbose_name='Destino')
    nome = models.CharField('Nome', max_length=120)
    endereco = models.CharField('Endereço', max_length=200, blank=True,
                                help_text='Onde a hospedagem fica.')
    imagem = models.ImageField('Imagem principal', upload_to='hospedagens/', blank=True, null=True)
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
    imagem = models.ImageField('Imagem', upload_to='hospedagens/galeria/')
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
                              help_text='Ex.: Dia 1 — Chegada em Santarém.')
    resumo = models.CharField('Resumo', max_length=200,
                              help_text='A linha que aparece com o dia fechado.')
    detalhe = models.TextField('Detalhe', blank=True,
                               help_text='O texto que abre quando a pessoa clica no dia.')
    imagem = models.ImageField('Foto do dia', upload_to='roteiro/', blank=True, null=True,
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
