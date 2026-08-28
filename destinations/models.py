from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Destino(models.Model):
    CONTINENTES = [
        ('AF', 'África'),
        ('AM', 'Américas'),
        ('AS', 'Ásia'),
        ('EU', 'Europa'),
        ('OC', 'Oceania'),
    ]

    nome = models.CharField('Nome', max_length=120)
    slug = models.SlugField('Slug', max_length=140, unique=True, blank=True,
                            help_text='Preenchido automaticamente a partir do nome.')
    pais = models.CharField('País', max_length=80)
    continente = models.CharField('Continente', max_length=2, choices=CONTINENTES, default='AM')
    descricao = models.TextField('Descrição')
    imagem_capa = models.ImageField('Imagem de capa', upload_to='destinos/', blank=True, null=True)
    preco_medio_diaria = models.DecimalField('Preço médio da diária (R$)', max_digits=8,
                                             decimal_places=2, blank=True, null=True)
    melhor_epoca = models.CharField('Melhor época para visitar', max_length=120, blank=True)
    destaque = models.BooleanField('Destaque na página inicial', default=False)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Destino'
        verbose_name_plural = 'Destinos'
        ordering = ['-destaque', 'nome']

    def __str__(self):
        return f'{self.nome}, {self.pais}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.nome}-{self.pais}')
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('destinations:detalhe', kwargs={'slug': self.slug})

    @property
    def media_avaliacoes(self):
        notas = [a.nota for a in self.avaliacoes.all()]
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
    TIPOS = [
        ('hotel', 'Hotel'),
        ('pousada', 'Pousada'),
        ('hostel', 'Hostel'),
        ('resort', 'Resort'),
        ('apartamento', 'Apartamento'),
        ('casa', 'Casa de temporada'),
    ]

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='hospedagens', verbose_name='Destino')
    nome = models.CharField('Nome', max_length=120)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPOS, default='hotel')
    descricao = models.TextField('Descrição', blank=True)
    preco_diaria = models.DecimalField('Preço da diária (R$)', max_digits=8, decimal_places=2)
    imagem = models.ImageField('Imagem principal', upload_to='hospedagens/', blank=True, null=True)
    endereco = models.CharField('Endereço', max_length=200, blank=True)
    site = models.URLField('Site', blank=True)
    disponivel = models.BooleanField('Disponível', default=True)

    class Meta:
        verbose_name = 'Hospedagem'
        verbose_name_plural = 'Hospedagens'
        ordering = ['preco_diaria']

    def __str__(self):
        return f'{self.nome} ({self.get_tipo_display()})'


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
