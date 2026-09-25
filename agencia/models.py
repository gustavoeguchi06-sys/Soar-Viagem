"""Orçamentos que as agências parceiras montam para os clientes delas.

O orçamento é da agência: ela registra o cliente, a viagem e o valor que passou,
e acompanha se o cliente aceitou. A Soar enxerga todos no painel do dono; cada
agência enxerga só os seus.
"""
from django.db import models
from django.utils import timezone

from destinations.models import Destino, Saida
from reservas.models import Reserva


class Orcamento(models.Model):
    STATUS = [
        ('enviado', 'Enviado ao cliente'),
        ('aceito', 'Aceito'),
        ('recusado', 'Recusado'),
    ]

    agencia = models.ForeignKey('contas.PerfilAgente', on_delete=models.CASCADE,
                                related_name='orcamentos', verbose_name='Agência')
    cliente_nome = models.CharField('Nome do cliente', max_length=120)
    cliente_telefone = models.CharField('Telefone/WhatsApp', max_length=20, blank=True)
    cliente_email = models.EmailField('E-mail do cliente', blank=True)
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT,
                                related_name='orcamentos', verbose_name='Destino')
    saida = models.ForeignKey(Saida, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='orcamentos', verbose_name='Data de saída',
                              help_text='Em branco, a data fica a combinar.')
    saida_texto = models.CharField('Saída', max_length=120, blank=True, editable=False)
    acomodacao = models.CharField('Acomodação', max_length=20,
                                  choices=Reserva.ACOMODACOES, default='casal')
    pessoas = models.PositiveSmallIntegerField('Quantidade de pessoas', default=2)
    valor = models.DecimalField('Valor total (R$)', max_digits=10, decimal_places=2,
                                null=True, blank=True,
                                help_text='O valor que a agência passou ao cliente.')
    validade = models.DateField('Válido até', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    status = models.CharField('Situação', max_length=10, choices=STATUS, default='enviado')
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-criado_em']

    def __str__(self):
        return '{} - {} ({})'.format(self.codigo, self.cliente_nome, self.destino.nome)

    def save(self, *args, **kwargs):
        # A data fica gravada em texto: se a saída for apagada depois, o
        # orçamento continua dizendo para quando foi.
        if self.saida_id:
            self.saida_texto = self.saida.texto
        super().save(*args, **kwargs)

    @property
    def codigo(self):
        return 'ORC-{:05d}'.format(self.pk or 0)

    @property
    def vencido(self):
        return (self.status == 'enviado' and self.validade is not None
                and self.validade < timezone.localdate())
