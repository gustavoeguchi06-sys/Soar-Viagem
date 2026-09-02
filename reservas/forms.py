from django import forms

from .models import Reserva

PESSOAS_POR_ACOMODACAO = {'single': 1, 'duplo': 2, 'triplo': 3}


class ReservaForm(forms.ModelForm):
    """Pedido de reserva. Quem preenche já está logado, então nome e e-mail
    vêm da conta — aqui só entra o que muda de viagem para viagem."""

    class Meta:
        model = Reserva
        fields = ['acomodacao', 'pessoas', 'telefone', 'observacao']
        widgets = {
            'acomodacao': forms.RadioSelect(),
            'pessoas': forms.NumberInput(attrs={'min': 1, 'max': 20}),
            'telefone': forms.TextInput(attrs={'placeholder': '(11) 90000-0000',
                                               'autocomplete': 'tel'}),
            'observacao': forms.Textarea(attrs={
                'rows': 3, 'maxlength': 1000,
                'placeholder': 'Restrição alimentar, quem viaja com você, dúvida sobre a data...'}),
        }

    def clean_pessoas(self):
        pessoas = self.cleaned_data['pessoas']
        if pessoas < 1:
            raise forms.ValidationError('Informe ao menos uma pessoa.')
        if pessoas > 20:
            raise forms.ValidationError(
                'Para grupos acima de 20 pessoas, fale direto com a Soar pelo WhatsApp.'
            )
        return pessoas

    def clean(self):
        """A acomodação escolhida tem que caber a quantidade de gente.

        Deixar passar 4 pessoas num quarto single geraria um pedido que a
        operadora não consegue atender — melhor avisar aqui.
        """
        dados = super().clean()
        acomodacao = dados.get('acomodacao')
        pessoas = dados.get('pessoas')
        cabem = PESSOAS_POR_ACOMODACAO.get(acomodacao)
        if cabem and pessoas and pessoas > cabem:
            self.add_error('pessoas', 'Essa acomodação é para até {} pessoa(s). '
                                      'Escolha outra ou reduza a quantidade.'.format(cabem))
        return dados
