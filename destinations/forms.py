from django import forms

from soar.mascaras import formatar_cep, formatar_telefone

from .models import Interessado


class InteresseForm(forms.ModelForm):
    """O "Saiba mais" do card da viagem, para quem não tem login."""

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

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.required = True

    def clean_whatsapp(self):
        return formatar_telefone(self.cleaned_data.get('whatsapp'))

    def clean_cep(self):
        return formatar_cep(self.cleaned_data.get('cep'))
