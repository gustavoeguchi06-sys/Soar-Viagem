"""Formulários de entrada e cadastro do viajante.

O site usa o `User` que já vem com o Django — não há model próprio aqui. O que
estes formulários fazem é falar português com o visitante e guardar o nome e o
e-mail, que a Soar precisa para tratar a pessoa pelo nome e responder a reserva.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class EntrarForm(AuthenticationForm):
    """Login por e-mail ou nome de usuário."""

    username = forms.CharField(
        label='E-mail ou usuário',
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username',
                                      'placeholder': 'voce@email.com'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password',
                                          'placeholder': 'Sua senha'}),
    )

    error_messages = {
        'invalid_login': 'E-mail/usuário ou senha não conferem. Confira e tente de novo.',
        'inactive': 'Esta conta está desativada. Fale com a Soar.',
    }

    def clean_username(self):
        """Deixa a pessoa entrar com o e-mail que ela cadastrou.

        O `authenticate` do Django procura pelo `username`; quando o que veio
        tem cara de e-mail, a gente troca pelo usuário correspondente antes.
        """
        digitado = self.cleaned_data['username'].strip()
        if '@' in digitado:
            usuario = User.objects.filter(email__iexact=digitado).first()
            if usuario:
                return usuario.username
        return digitado


class CadastroForm(UserCreationForm):
    """Criação da conta do cliente."""

    first_name = forms.CharField(
        label='Nome', max_length=60,
        widget=forms.TextInput(attrs={'placeholder': 'Como podemos te chamar'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'voce@email.com',
                                       'autocomplete': 'email'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'email', 'username']
        labels = {'username': 'Nome de usuário'}
        help_texts = {'username': 'Letras, números e @ . + - _ — é com ele que você entra.'}
        widgets = {'username': forms.TextInput(attrs={'placeholder': 'seu.usuario'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Repita a senha'
        self.fields['password1'].widget.attrs['placeholder'] = 'Mínimo de 8 caracteres'
        self.fields['password2'].widget.attrs['placeholder'] = 'A mesma senha de novo'

    def clean_email(self):
        """Dois cadastros com o mesmo e-mail quebrariam o login por e-mail."""
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Já existe uma conta com este e-mail. Tente entrar ou use outro endereço.'
            )
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.first_name = self.cleaned_data['first_name'].strip()
        if commit:
            usuario.save()
        return usuario
