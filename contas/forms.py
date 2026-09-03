"""Formulários de entrada e cadastro do viajante.

O site usa o `User` que já vem com o Django — não há model próprio aqui. O que
estes formulários fazem é falar português com o visitante e guardar o nome e o
e-mail, que a Soar precisa para tratar a pessoa pelo nome e responder a reserva.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe


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
        # Só chega aqui quem acertou a senha (o backend é o AllowAllUsersModelBackend),
        # então dizer o motivo não revela nada a quem está tentando adivinhar.
        'inactive': 'Falta confirmar seu e-mail. Procure a mensagem que enviamos no '
                    'cadastro — o link de confirmação está nela.',
    }

    def clean_username(self):
        """Deixa a pessoa entrar com o e-mail que ela cadastrou.

        O `authenticate` do Django procura pelo `username`; quando o que veio
        tem cara de e-mail, a gente troca pelo usuário correspondente antes.
        Um índice único no banco garante que existe no máximo um usuário por
        e-mail (ver contas/migrations/0001_email_unico.py).
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
    aceite_privacidade = forms.BooleanField(
        required=True,
        error_messages={'required': 'É preciso aceitar o aviso de privacidade para criar a conta.'},
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
        # O rótulo é montado aqui, e não no corpo da classe, porque resolver a
        # URL na hora do import roda antes das rotas existirem.
        self.fields['aceite_privacidade'].label = mark_safe(
            'Li e aceito o <a href="{}" target="_blank" rel="noopener">aviso de '
            'privacidade</a> e autorizo a Soar a usar meus dados para organizar '
            'a viagem.'.format(reverse('contas:privacidade'))
        )

    def clean_email(self):
        """Normaliza o endereço.

        Note o que **não** acontece aqui: o formulário não recusa mais um e-mail
        já cadastrado. Aquela mensagem confirmava, para qualquer visitante, se
        um endereço tinha conta no site — bastava um script com uma lista de
        e-mails para saber quem é cliente da Soar. Quem trata a duplicata agora
        é a view, avisando por e-mail o dono do endereço, e a resposta na tela é
        a mesma dos dois jeitos.
        """
        return self.cleaned_data['email'].strip().lower()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.first_name = self.cleaned_data['first_name'].strip()
        # Só vira conta de verdade depois de clicar no link do e-mail.
        usuario.is_active = False
        if commit:
            usuario.save()
        return usuario


class ExcluirContaForm(forms.Form):
    """Confirmação da exclusão da própria conta (LGPD, art. 18).

    Pede a senha porque a exclusão é definitiva: sem isso, bastaria um
    computador destravado para alguém apagar o histórico da pessoa.
    """

    senha = forms.CharField(
        label='Confirme sua senha',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    confirmacao = forms.BooleanField(
        label='Entendo que meus dados e minhas reservas serão apagados e que não dá para desfazer.',
        required=True,
    )

    def __init__(self, usuario, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_senha(self):
        senha = self.cleaned_data['senha']
        if not self.usuario.check_password(senha):
            raise forms.ValidationError('Senha incorreta.')
        return senha
