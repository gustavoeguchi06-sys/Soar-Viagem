from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .models import Avaliacao

# A foto é o único arquivo que entra pela frente do site. Quem envia já tem
# conta (a view exige login), mas o arquivo continua vindo de fora: confere
# tamanho e formato antes de gravar qualquer coisa em disco.
FORMATOS_ACEITOS = {'JPEG', 'PNG', 'WEBP', 'GIF'}
EXTENSOES_ACEITAS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
# A extensão gravada sai do formato que o Pillow reconheceu, não do nome que o
# navegador mandou: um PNG chamado "foto.gif" é gravado como .png, e o servidor
# web entrega com o tipo certo.
EXTENSAO_DO_FORMATO = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp', 'GIF': '.gif'}


class AvaliacaoForm(forms.ModelForm):
    """Avaliação de um destino.

    `nome_autor` saiu do formulário de propósito: era campo livre e permitia
    assinar com o nome de outra pessoa — ou da própria operadora. Agora a view
    preenche a partir da conta.
    """

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario', 'foto']
        widgets = {
            'nota': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000,
                                                'placeholder': 'Conte como foi sua experiência...'}),
            'foto': forms.ClearableFileInput(attrs={'accept': ','.join(EXTENSOES_ACEITAS)}),
        }

    def clean_comentario(self):
        comentario = self.cleaned_data['comentario'].strip()
        if len(comentario) < 10:
            raise forms.ValidationError('Conte um pouco mais: escreva ao menos 10 caracteres.')
        return comentario[:2000]

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if not foto:
            return foto

        # arquivo já salvo (edição) não é upload novo: nada para conferir
        if not isinstance(foto, UploadedFile):
            return foto

        limite = settings.TAMANHO_MAXIMO_FOTO
        if foto.size > limite:
            raise forms.ValidationError(
                'A foto tem {:.1f} MB. O limite é de {} MB.'.format(
                    foto.size / (1024 * 1024), limite // (1024 * 1024))
            )

        # O ImageField do Django já abre o arquivo com o Pillow e recusa o que
        # não for imagem; aqui a gente restringe também quais formatos entram.
        formato = getattr(foto, 'image', None)
        formato = (getattr(formato, 'format', None) or '').upper()
        if formato not in FORMATOS_ACEITOS:
            raise forms.ValidationError(
                'Formato {} não aceito. Envie JPG, PNG, WEBP ou GIF.'.format(formato or 'desconhecido')
            )
        # O nome é descartado de qualquer jeito (reviews.models.caminho_foto_avaliacao
        # sorteia outro); aqui só a extensão é acertada ao conteúdo.
        foto.name = 'foto' + EXTENSAO_DO_FORMATO[formato]
        return foto
