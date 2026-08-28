from django import forms

from .models import Avaliacao


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['nome_autor', 'nota', 'comentario', 'foto']
        widgets = {
            'nome_autor': forms.TextInput(attrs={'placeholder': 'Como você quer aparecer'}),
            'nota': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Conte como foi sua experiência...'}),
        }
