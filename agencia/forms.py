from django import forms
from django.utils import timezone

from destinations.admin import CampoPreco
from destinations.models import Destino, Saida
from reservas.models import Reserva

from .models import Orcamento

DATA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class OrcamentoForm(forms.ModelForm):
    """Orçamento montado pela agência.

    A data de saída vem das saídas cadastradas pela Soar, agrupadas por destino
    (o JavaScript da tela mostra só as do destino escolhido). Com o JavaScript
    desligado continua funcionando: o `clean` recusa uma data de outro destino.
    """

    saida_escolhida = forms.ChoiceField(label='Data de saída', required=False)
    valor = CampoPreco(label='Valor total (R$)', required=False, max_digits=10,
                       decimal_places=2, help_text='O valor que você passou ao cliente.')

    class Meta:
        model = Orcamento
        fields = ['cliente_nome', 'cliente_telefone', 'cliente_email', 'destino',
                  'saida_escolhida', 'acomodacao', 'pessoas', 'valor', 'validade',
                  'observacoes', 'status']
        widgets = {
            'validade': DATA,
            'pessoas': forms.NumberInput(attrs={'min': 1, 'max': 60}),
            'cliente_telefone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000',
                                                       'autocomplete': 'off'}),
            'observacoes': forms.Textarea(attrs={
                'rows': 3, 'maxlength': 2000,
                'placeholder': 'Condições combinadas, forma de pagamento, pedidos do cliente...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destino'].queryset = Destino.objects.order_by('nome')
        self.fields['destino'].empty_label = 'Escolha o destino'
        # Só o nome: o JavaScript da tela casa este texto com o grupo de datas.
        self.fields['destino'].label_from_instance = lambda destino: destino.nome
        self.fields['validade'].input_formats = ['%Y-%m-%d']
        self.fields['valor'].widget.attrs.pop('style', None)

        saidas = Saida.objects.filter(data_ida__gte=timezone.localdate())
        atual = self.instance.saida if self.instance.pk else None
        if atual is not None:
            saidas = saidas | Saida.objects.filter(pk=atual.pk)
        self._saidas = {str(s.pk): s for s in saidas.select_related('destino')
                        .order_by('destino__nome', 'data_ida')}

        grupos = {}
        for chave, s in self._saidas.items():
            grupos.setdefault(s.destino.nome, []).append((chave, s.texto))
        self.fields['saida_escolhida'].choices = (
            [('', 'A combinar')] + [(nome, opcoes) for nome, opcoes in grupos.items()])
        if atual is not None:
            self.initial['saida_escolhida'] = str(atual.pk)

    def clean_pessoas(self):
        pessoas = self.cleaned_data['pessoas']
        if not 1 <= pessoas <= 60:
            raise forms.ValidationError('Informe de 1 a 60 pessoas.')
        return pessoas

    def clean(self):
        dados = super().clean()
        saida = self._saidas.get(dados.get('saida_escolhida') or '')
        destino = dados.get('destino')
        if saida and destino and saida.destino_id != destino.pk:
            self.add_error('saida_escolhida', 'Essa data é de outro destino. Escolha uma '
                                              'data de {}.'.format(destino.nome))
        self.instance.saida = saida
        if saida is None:
            self.instance.saida_texto = ''
        return dados


class AtendimentoForm(forms.ModelForm):
    """O que a agência muda numa reserva do cliente dela."""

    class Meta:
        model = Reserva
        fields = ['status', 'nota_agencia']
        widgets = {
            'nota_agencia': forms.Textarea(attrs={
                'rows': 4, 'maxlength': 2000,
                'placeholder': 'Ex.: liguei dia 25, cliente vai pagar no Pix até sexta.'}),
        }
        labels = {'status': 'Situação do pedido'}
