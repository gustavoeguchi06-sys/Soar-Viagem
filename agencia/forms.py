import re

from django import forms

from soar.mascaras import formatar_telefone

from .models import Orcamento

MAX_CRIANCAS = 10
MAX_ADULTOS = 60
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


class OrcamentoViagemForm(forms.ModelForm):
    """Orçamento que a agência monta no card da página da viagem.

    O destino é o da página e as datas são as saídas dela que ainda têm vaga.
    O valor não é digitado: a view calcula pela tabela da viagem.

    Quartos: para cada tipo da viagem, quantos quartos e quantas pessoas
    (campos quartos_<tipo> e pessoas_<tipo>). Dá para escolher vários tipos e
    vários quartos de cada um; cada quarto leva de 1 pessoa até a lotação dele
    (Duplo até 2, Triplo até 3), nunca mais. Single é sempre 1 por quarto.
    """

    saida = forms.ChoiceField(label='Data de saída', required=False,
                              error_messages={'invalid_choice': 'Escolha uma das datas da viagem.'})
    # só para mostrar o erro do conjunto ("escolha pelo menos um quarto") embaixo dos quartos
    escolha_quartos = forms.CharField(required=False, widget=forms.HiddenInput)

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

    def __init__(self, *args, destino, **kwargs):
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

        from destinations.conteudo import _acomodacoes
        self._acomodacoes = _acomodacoes(destino)
        for a in self._acomodacoes:
            # sem nada vindo do envio, já vem 1 quarto do tipo padrão (casal), lotado
            um = 1 if a['padrao'] else 0
            self.fields['quartos_' + a['chave']] = forms.IntegerField(
                label='Quartos', required=False, min_value=0, max_value=MAX_ADULTOS, initial=um,
                widget=forms.NumberInput(attrs={'min': 0, 'max': MAX_ADULTOS,
                                                'inputmode': 'numeric'}))
            if a['capacidade'] > 1:
                self.fields['pessoas_' + a['chave']] = forms.IntegerField(
                    label='Pessoas', required=False, min_value=0, max_value=MAX_ADULTOS,
                    initial=um * a['capacidade'],
                    widget=forms.NumberInput(attrs={'min': 0, 'max': MAX_ADULTOS,
                                                    'inputmode': 'numeric'}))

    @property
    def quartos_campos(self):
        """Uma linha por tipo de quarto da viagem, com os campos de quartos e pessoas."""
        return [{'a': a, 'quartos': self['quartos_' + a['chave']],
                 'pessoas': self['pessoas_' + a['chave']] if a['capacidade'] > 1 else None}
                for a in self._acomodacoes]

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

        escolhidos = []
        for a in self._acomodacoes:
            chave, lotacao, nome = a['chave'], a['capacidade'], a['nome']
            quartos = dados.get('quartos_' + chave) or 0
            # Single: uma pessoa por quarto, sem campo de pessoas
            pessoas = (dados.get('pessoas_' + chave) or 0) if lotacao > 1 else quartos
            if not quartos:
                if pessoas:
                    self.add_error('pessoas_' + chave, 'Escolha quantos quartos antes das pessoas.')
                continue
            # o tipo que o dono marcou com 0 nesta data acabou; com número, é o limite
            disponiveis = getattr(saida, 'quartos_' + chave, None) if saida else None
            if disponiveis == 0:
                self.add_error('quartos_' + chave, 'Esse quarto está esgotado nesta data.')
            elif disponiveis is not None and quartos > disponiveis:
                self.add_error('quartos_' + chave, 'Nesta data há só {} quarto{} {}.'.format(
                    disponiveis, 's' if disponiveis != 1 else '', nome))
            if pessoas < quartos:
                self.add_error('pessoas_' + chave, 'Cada quarto precisa de pelo menos 1 pessoa: '
                               'com {0} quartos, no mínimo {0} pessoas.'.format(quartos))
            elif pessoas > quartos * lotacao:
                self.add_error('pessoas_' + chave, 'O {} leva até {} pessoas por quarto: com {} '
                               'quarto{}, no máximo {}.'.format(
                                   nome, lotacao, quartos, 's' if quartos != 1 else '',
                                   quartos * lotacao))
            escolhidos.append({'tipo': chave, 'quartos': quartos, 'pessoas': pessoas,
                               'preco': str(a['valor']) if a['valor'] is not None else None})

        total = sum(q['pessoas'] for q in escolhidos)
        if not escolhidos:
            self.add_error('escolha_quartos', 'Escolha pelo menos um quarto.')
        elif total > MAX_ADULTOS:
            self.add_error('escolha_quartos',
                           'No máximo {} adultos por orçamento.'.format(MAX_ADULTOS))
        else:
            self.instance.quartos = escolhidos
            self.instance.pessoas = total
            self.instance.acomodacao = escolhidos[0]['tipo']
        return dados
