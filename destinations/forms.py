from django import forms

from soar.mascaras import formatar_cep, formatar_telefone

from .escolha_quartos import EscolhaDeQuartos
from .models import Interessado


class InteresseForm(EscolhaDeQuartos, forms.ModelForm):
    """O "Saiba mais" do card da viagem, para quem não tem login.

    Vai junto o que a pessoa marcou no card: a data e os quartos, com quantas
    pessoas em cada um (destinations/escolha_quartos.py).
    """

    saida = forms.ChoiceField(label='Data de saída', required=False,
                              error_messages={'invalid_choice': 'Escolha uma das datas da viagem.'})

    class Meta:
        model = Interessado
        fields = ['nome', 'email', 'whatsapp', 'cep']
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'name', 'maxlength': 120}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email',
                                             'placeholder': 'voce@email.com'}),
            'whatsapp': forms.TextInput(attrs={'placeholder': '(11) 90000-0000',
                                               'inputmode': 'tel', 'autocomplete': 'tel',
                                               'data-mascara': 'telefone'}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000', 'inputmode': 'numeric',
                                          'autocomplete': 'postal-code',
                                          'data-mascara': 'cep'}),
        }

    def __init__(self, *args, destino, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.required = True
        self.fields['saida'].required = False
        self._saidas = {str(s.pk): s for s in destino.saidas_futuras if not s.esgotada}
        self.fields['saida'].choices = [('', 'A combinar')] + [
            (chave, s.texto) for chave, s in self._saidas.items()]
        self.criar_campos_de_quartos(destino)

    @property
    def erro_no_contato(self):
        """Com erro nos dados de contato, o "Saiba mais" já volta aberto."""
        return any(campo.errors for campo in self.campos_de_contato)

    @property
    def campos_de_contato(self):
        """Os campos que aparecem ao abrir o "Saiba mais" (os quartos ficam no card)."""
        return [self[nome] for nome in ('nome', 'email', 'whatsapp', 'cep')]

    def clean(self):
        dados = super().clean()
        self.instance.saida = saida = self._saidas.get(dados.get('saida') or '')
        self.conferir_quartos(dados, saida, obrigatorio=False)
        if self.quartos_escolhidos:
            self.instance.quartos = self.quartos_escolhidos
            self.instance.pessoas = sum(q['pessoas'] for q in self.quartos_escolhidos)
        return dados

    def clean_whatsapp(self):
        return formatar_telefone(self.cleaned_data.get('whatsapp'))

    def clean_cep(self):
        return formatar_cep(self.cleaned_data.get('cep'))
