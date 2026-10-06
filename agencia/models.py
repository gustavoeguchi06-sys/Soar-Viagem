"""Orçamentos que as agências parceiras montam para os clientes delas.

A agência monta o orçamento direto no card da página da viagem, sem abrir o
painel: escolhe a data, a acomodação, quantos adultos e as idades das crianças,
e o valor sai da tabela da viagem. Vale por 72 horas. A Soar enxerga todos no
painel do dono.
"""
from datetime import timedelta

from django.db import models
from django.utils import timezone

from destinations.models import Destino, Saida

# Os mesmos tipos de quarto da página da viagem (destinations/quartos.py), com
# o rótulo que aparece no orçamento e no PDF.
ACOMODACOES = [
    ('single', 'Single: 1 pessoa'),
    ('casal', 'Casal: 2 pessoas'),
    ('duplo', 'Duplo (Twin): 2 pessoas'),
    ('triplo', 'Triplo: 3 pessoas'),
]

VALIDADE = timedelta(hours=72)

AVISO = ('Este orçamento não garante a reserva ou a disponibilidade dos serviços '
         'apresentados.',
         'A cotação é válida por 72 horas, estando sujeita à disponibilidade e à '
         'alteração de valores após esse período.')


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
                                  choices=ACOMODACOES, default='casal',
                                  help_text='O primeiro tipo de quarto escolhido (os outros '
                                            'estão em "quartos").')
    pessoas = models.PositiveSmallIntegerField('Adultos', default=2,
                                               help_text='Soma das pessoas de todos os quartos.')
    # Os quartos escolhidos: [{"tipo": "duplo", "quartos": 2, "pessoas": 3,
    # "preco": "3588.00"}, ...]. Cada tipo aceita de 1 pessoa até a lotação do
    # quarto; o valor é o preço por pessoa do tipo vezes as pessoas nele.
    # Orçamento antigo (de antes de dar para escolher vários quartos) fica vazio.
    quartos = models.JSONField('Quartos', default=list, blank=True)
    # Criança (CHD) não é acomodação: viaja junto com os adultos, no quarto
    # deles, e o preço depende da idade. Guardado como "4, 7".
    idades_criancas = models.CharField(
        'Idades das crianças (CHD)', max_length=60, blank=True,
        help_text='De 0 a 8 anos, separadas por vírgula, ex.: 4, 7. Em branco se não vai criança.')
    valor = models.DecimalField('Valor total (R$)', max_digits=10, decimal_places=2,
                                null=True, blank=True,
                                help_text='Adultos pela tabela da viagem; crianças sob consulta.')
    valido_ate = models.DateTimeField('Válido até', null=True, blank=True,
                                      help_text='72 horas depois de criado.')
    enviado_em = models.DateTimeField('PDF enviado por e-mail em', null=True, blank=True,
                                      help_text='Em branco: o e-mail não saiu.')
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
        if self.valido_ate is None:
            self.valido_ate = timezone.now() + VALIDADE
        # A data fica gravada em texto: se a saída for apagada depois, o
        # orçamento continua dizendo para quando foi.
        if self.saida_id:
            self.saida_texto = self.saida.texto
        super().save(*args, **kwargs)

    @property
    def codigo(self):
        return 'ORC-{:05d}'.format(self.pk or 0)

    @property
    def criancas(self):
        """'4, 7' -> [4, 7]"""
        return [int(i) for i in self.idades_criancas.split(',') if i.strip()]

    @property
    def criancas_texto(self):
        """[4, 7] -> '2 (4 e 7 anos)'; [1] -> '1 (1 ano)'"""
        idades = self.criancas
        if not idades:
            return ''
        lista = ', '.join(str(i) for i in idades[:-1])
        lista = '{} e {}'.format(lista, idades[-1]) if lista else str(idades[-1])
        return '{} ({} {})'.format(len(idades), lista, 'ano' if idades == [1] else 'anos')

    @property
    def linhas_de_quartos(self):
        """[{'nome': 'Duplo (Twin)', 'quartos': 2, 'pessoas': 3, 'preco': Decimal}, ...]"""
        from decimal import Decimal

        from destinations.quartos import POR_CHAVE
        linhas = []
        for q in self.quartos or []:
            tipo = POR_CHAVE.get(q.get('tipo'))
            if tipo is None:
                continue
            linhas.append({'nome': tipo['nome'], 'quartos': q.get('quartos'),
                           'pessoas': q.get('pessoas'),
                           'preco': Decimal(q['preco']) if q.get('preco') else None})
        return linhas

    @property
    def acomodacao_texto(self):
        """'2 quartos Duplo (Twin), 3 pessoas; 1 quarto Single, 1 pessoa'"""
        from destinations.escolha_quartos import texto_dos_quartos
        # orçamento antigo (sem a lista de quartos): um tipo só
        return texto_dos_quartos(self.quartos) or self.get_acomodacao_display()

    @property
    def vencido(self):
        return (self.status == 'enviado' and self.valido_ate is not None
                and self.valido_ate < timezone.now())
