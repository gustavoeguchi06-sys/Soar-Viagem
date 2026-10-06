import re

from django import forms

from destinations.escolha_quartos import EscolhaDeQuartos
from soar.mascaras import formatar_telefone

from .models import Orcamento

MAX_CRIANCAS = 10
IDADE_MAXIMA_CHD = 8   # acima disso já paga como adulto


def idades_das_criancas(texto):
    """'4, 7' (ou '4 e 7', '4;7') -> [4, 7]. Algo que não é idade de CHD (0 a 8) -> None."""
    partes = re.split(r'[,;/\s]+|\be\b', (texto or '').strip())
    idades = []
    for parte in filter(None, partes):
        if not parte.isdigit() or int(parte) > IDADE_MAXIMA_CHD:
            return None
        idades.append(int(parte))
    return idades


class OrcamentoViagemForm(EscolhaDeQuartos, forms.ModelForm):
    """Orçamento que a agência monta no card da página da viagem.

    O destino é o da página e as datas são as saídas dela que ainda têm vaga.
    O valor não é digitado: a view calcula pela tabela da viagem.

    Quartos: vários tipos e vários quartos de cada um, de 1 pessoa até a
    lotação (destinations/escolha_quartos.py).
    """

    saida = forms.ChoiceField(label='Data de saída', required=False,
                              error_messages={'invalid_choice': 'Escolha uma das datas da viagem.'})

    class Meta:
        model = Orcamento
        fields = ['cliente_nome', 'cliente_email', 'cliente_telefone', 'idades_criancas']
        labels = {'cliente_nome': 'Nome do responsável',
                  'cliente_email': 'E-mail para enviar o orçamento',
                  'cliente_telefone': 'WhatsApp (opcional)',
                  'idades_criancas': 'Idades das crianças'}
        widgets = {
            'cliente_nome': forms.TextInput(attrs={'autocomplete': 'off', 'maxlength': 120}),
            'cliente_email': forms.EmailInput(attrs={'autocomplete': 'off',
                                                     'placeholder': 'cliente@gmail.com'}),
            'cliente_telefone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000',
                                                       'inputmode': 'tel', 'data-mascara': 'telefone',
                                                       'autocomplete': 'off'}),
            'idades_criancas': forms.TextInput(attrs={'placeholder': 'Ex.: 4, 7',
                                                      'autocomplete': 'off'}),
        }

    def __init__(self, *args, destino, quartos_iniciais=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente_nome'].error_messages['required'] = 'Informe o nome do responsável.'
        # o PDF vai para este endereço: sem ele não há para onde mandar
        self.fields['cliente_email'].required = True
        self.fields['cliente_email'].error_messages.update(
            required='Informe o e-mail para onde vai o orçamento.',
            invalid='Esse e-mail não parece certo. Confira e tente de novo.')
        self._saidas = {str(s.pk): s for s in destino.saidas_futuras if not s.esgotada}
        self.fields['saida'].choices = [('', 'A combinar')] + [
            (chave, s.texto) for chave, s in self._saidas.items()]

        self.criar_campos_de_quartos(destino, quartos_iniciais)

    @property
    def campos_do_popup(self):
        """O que a agência preenche no pop-up que abre em "Criar orçamento"."""
        return [self['cliente_nome'], self['cliente_email'], self['cliente_telefone']]

    @property
    def erro_no_popup(self):
        """Com erro num destes campos, o pop-up já abre de novo ao voltar a página."""
        return any(campo.errors for campo in self.campos_do_popup) or bool(self.non_field_errors())

    def clean_cliente_telefone(self):
        return formatar_telefone(self.cleaned_data.get('cliente_telefone'))

    def clean_idades_criancas(self):
        idades = idades_das_criancas(self.cleaned_data.get('idades_criancas'))
        if idades is None:
            raise forms.ValidationError('Digite só as idades, de 0 a {} anos, separadas por '
                                        'vírgula. Ex.: 4, 7'.format(IDADE_MAXIMA_CHD))
        if len(idades) > MAX_CRIANCAS:
            raise forms.ValidationError('No máximo {} crianças por orçamento.'.format(MAX_CRIANCAS))
        return ', '.join(str(i) for i in idades)

    def clean(self):
        dados = super().clean()
        self.instance.saida = saida = self._saidas.get(dados.get('saida') or '')

        self.conferir_quartos(dados, saida)
        if self.quartos_escolhidos:
            self.instance.quartos = self.quartos_escolhidos
            self.instance.pessoas = sum(q['pessoas'] for q in self.quartos_escolhidos)
            self.instance.acomodacao = self.quartos_escolhidos[0]['tipo']
        return dados
