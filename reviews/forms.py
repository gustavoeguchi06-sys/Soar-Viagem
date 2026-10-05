"""Avaliação enviada pelo visitante na página da viagem.

Qualquer pessoa pode avaliar, sem conta. Por isso a avaliação entra na fila
(publicada=False) e só aparece no site depois que o dono aprova no painel.
"""
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Avaliacao

NOTAS = [(5, '5 estrelas: excelente'), (4, '4 estrelas: muito boa'), (3, '3 estrelas: boa'),
         (2, '2 estrelas: regular'), (1, '1 estrela: ruim')]


class AvaliacaoForm(forms.ModelForm):
    nota = forms.TypedChoiceField(label='Sua nota', choices=NOTAS, coerce=int, initial=5)
    # Campo escondido por CSS: pessoa não preenche, robô de spam preenche.
    site = forms.CharField(required=False, label='Deixe em branco',
                           widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))
    aceite = forms.BooleanField(
        required=True,
        error_messages={'required': 'É preciso autorizar a publicação para enviar a avaliação.'})

    class Meta:
        model = Avaliacao
        fields = ['nome_autor', 'nota', 'comentario', 'foto']
        labels = {
            'nome_autor': 'Seu nome',
            'comentario': 'Como foi a viagem?',
            'foto': 'Uma foto da viagem (opcional)',
        }
        help_texts = {
            'nome_autor': 'Como vai aparecer no site, ex.: Ana S.',
            'foto': 'JPG, PNG ou WebP, até 10 MB.',
        }
        widgets = {
            'nome_autor': forms.TextInput(attrs={'autocomplete': 'name', 'maxlength': 80}),
            'comentario': forms.Textarea(attrs={'rows': 4, 'maxlength': 1500}),
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        # O rótulo com link é montado aqui: resolver a URL na hora do import
        # roda antes de as rotas existirem.
        self.fields['aceite'].label = mark_safe(
            'Autorizo a Soar a publicar meu nome, a nota e o comentário no site '
            '(<a href="{}" target="_blank" rel="noopener">aviso de privacidade</a>).'.format(
                reverse('contas:privacidade')))
        self.order_fields(['nome_autor', 'nota', 'comentario', 'foto', 'aceite', 'site'])

    def clean_comentario(self):
        texto = (self.cleaned_data.get('comentario') or '').strip()
        if len(texto) < 10:
            raise forms.ValidationError('Conte um pouco mais sobre a viagem (pelo menos 10 letras).')
        return texto[:1500]

    def clean_nome_autor(self):
        return (self.cleaned_data.get('nome_autor') or '').strip()

    def eh_robo(self):
        return bool(self.cleaned_data.get('site'))
