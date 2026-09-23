"""N6 — a foto da avaliação ganha nome sorteado e extensão do formato real."""
import io
import re

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from reviews.forms import AvaliacaoForm
from reviews.models import caminho_foto_avaliacao


def _imagem(formato):
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), 'green').save(buffer, format=formato)
    return buffer.getvalue()


class FotoDaAvaliacaoTests(TestCase):

    def _form(self, nome, conteudo):
        return AvaliacaoForm(data={'nota': 5, 'comentario': 'Viagem excelente, recomendo.'},
                             files={'foto': SimpleUploadedFile(nome, conteudo)})

    def test_extensao_vem_do_conteudo_e_nao_do_nome(self):
        form = self._form('IMG_2031.gif', _imagem('PNG'))   # PNG disfarçado de GIF
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['foto'].name, 'foto.png')

    def test_nome_gravado_e_sorteado(self):
        caminho = caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg')
        self.assertRegex(caminho, r'^avaliacoes/[0-9a-f]{32}\.jpg$')
        self.assertNotIn('joao', caminho)
        self.assertNotEqual(caminho, caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg'))

    def test_extensao_perigosa_nunca_e_gravada(self):
        self.assertTrue(re.fullmatch(r'avaliacoes/[0-9a-f]{32}',
                                     caminho_foto_avaliacao(None, 'x.html')))

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        form = self._form('foto.jpg', b'<script>alert(1)</script>')
        self.assertFalse(form.is_valid())
        self.assertIn('foto', form.errors)
