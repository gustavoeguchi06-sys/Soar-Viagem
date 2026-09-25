from django.contrib.auth.models import User
from django.db import models

from destinations.models import Destino


class Reserva(models.Model):
    """Pedido de reserva feito por um cliente logado.

    Não é uma venda: o site não cobra nada (o pagamento sai do fluxo online de
    propósito). É o pedido que chega para a Soar, que confirma e combina o
    pagamento com a pessoa. Por isso o preço fica gravado como *estimativa* do
    dia do pedido — se a tabela mudar depois, o que foi combinado não se perde.
    """

    ACOMODACOES = [
        ('single', 'Single: 1 pessoa'),
        ('casal', 'Casal: 2 pessoas'),
        ('duplo', 'Duplo (Twin): 2 pessoas'),
        ('triplo', 'Triplo: 3 pessoas'),
        ('crianca', 'Criança até 8 anos (não paga)'),
    ]

    STATUS = [
        ('pendente', 'Aguardando contato'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    # SET_NULL, e não CASCADE: quando o cliente exclui a conta, a reserva
    # continua existindo — anonimizada — pelo prazo fiscal. Com CASCADE a
    # exclusão da conta apagava as reservas junto, contra o que o aviso de
    # privacidade promete e a legislação exige.
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='reservas', verbose_name='Cliente')
    destino = models.ForeignKey(Destino, on_delete=models.PROTECT,
                                related_name='reservas', verbose_name='Destino')
    acomodacao = models.CharField('Acomodação', max_length=20,
                                  choices=ACOMODACOES, default='casal')
    pessoas = models.PositiveSmallIntegerField('Quantidade de pessoas', default=1)
    telefone = models.CharField('Telefone/WhatsApp', max_length=20, blank=True)
    observacao = models.TextField('Observações', blank=True)
    preco_estimado = models.DecimalField('Preço estimado por pessoa (R$)', max_digits=9,
                                         decimal_places=2, blank=True, null=True)
    saida = models.CharField('Saída pedida', max_length=120, blank=True,
                             help_text='Período que estava anunciado quando o cliente reservou.')
    status = models.CharField('Situação', max_length=12, choices=STATUS, default='pendente')
    # A agência parceira que atende este cliente: preenchida quando ele chegou
    # ao site pelo link de indicação dela, ou pelo dono no painel. É o que faz
    # a reserva aparecer no painel da agência, e só no dela.
    agencia = models.ForeignKey('contas.PerfilAgente', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='reservas',
                                verbose_name='Agência parceira')
    nota_agencia = models.TextField(
        'Anotações do atendimento', blank=True,
        help_text='Escritas pela agência ou pela Soar. O cliente não vê.')
    criado_em = models.DateTimeField('Pedido em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-criado_em']

    def __str__(self):
        return '{} - {} ({})'.format(self.codigo, self.destino.nome, self.get_status_display())

    @property
    def codigo(self):
        """Código curto que o cliente informa quando fala com a operadora."""
        return 'SOAR-{:05d}'.format(self.pk or 0)

    @property
    def total_estimado(self):
        if self.preco_estimado is None:
            return None
        return self.preco_estimado * self.pessoas
