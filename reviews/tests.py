"""A foto da avaliação ganha nome sorteado, e só imagem de verdade entra."""
import re

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from reviews.models import Avaliacao, caminho_foto_avaliacao


class FotoDaAvaliacaoTests(TestCase):
    """A avaliação é cadastrada pelo dono no painel; estas regras valem lá."""

    def test_nome_gravado_e_sorteado(self):
        caminho = caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg')
        self.assertRegex(caminho, r'^avaliacoes/[0-9a-f]{32}\.jpg$')
        self.assertNotIn('joao', caminho)
        self.assertNotEqual(caminho, caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg'))

    def test_extensao_perigosa_nunca_e_gravada(self):
        self.assertTrue(re.fullmatch(r'avaliacoes/[0-9a-f]{32}',
                                     caminho_foto_avaliacao(None, 'x.html')))

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        campo = Avaliacao._meta.get_field('foto')
        falso = SimpleUploadedFile('foto.jpg', b'<script>alert(1)</script>')
        with self.assertRaises(ValidationError):
            campo.formfield().clean(falso)
