from django import forms

from .models import Avaliacao

# O formulário de avaliação é público: qualquer visitante posta sem login e
# pode anexar uma foto. Por isso o arquivo passa por conferência de tamanho e
# de formato antes de ser aceito.
TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024      # 5 MB
FORMATOS_ACEITOS = {'JPEG', 'PNG', 'WEBP', 'GIF'}
EXTENSOES_ACEITAS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['nome_autor', 'nota', 'comentario', 'foto']
        widgets = {
            'nome_autor': forms.TextInput(attrs={'placeholder': 'Como você quer aparecer',
                                                 'maxlength': 80}),
            'nota': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000,
                                                'placeholder': 'Conte como foi sua experiência...'}),
            'foto': forms.ClearableFileInput(attrs={'accept': ','.join(EXTENSOES_ACEITAS)}),
        }

    def clean_nome_autor(self):
        nome = self.cleaned_data['nome_autor'].strip()
        if len(nome) < 2:
            raise forms.ValidationError('Escreva seu nome com pelo menos 2 letras.')
        return nome

    def clean_comentario(self):
        comentario = self.cleaned_data['comentario'].strip()
        if len(comentario) < 10:
            raise forms.ValidationError('Conte um pouco mais: escreva ao menos 10 caracteres.')
        return comentario[:2000]

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if not foto:
            return foto

        # arquivo já salvo (edição) não traz tamanho novo para conferir
        if not hasattr(foto, 'size'):
            return foto

        if foto.size > TAMANHO_MAXIMO_FOTO:
            raise forms.ValidationError(
                'A foto tem {:.1f} MB. O limite é de {} MB.'.format(
                    foto.size / (1024 * 1024), TAMANHO_MAXIMO_FOTO // (1024 * 1024))
            )

        # O ImageField do Django já abre o arquivo com o Pillow e recusa o que
        # não for imagem; aqui a gente restringe também quais formatos entram.
        formato = getattr(foto, 'image', None)
        formato = getattr(formato, 'format', None)
        if formato and formato.upper() not in FORMATOS_ACEITOS:
            raise forms.ValidationError(
                'Formato {} não aceito. Envie JPG, PNG, WEBP ou GIF.'.format(formato)
            )
        return foto
