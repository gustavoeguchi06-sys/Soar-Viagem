"""Aviso de foto pequena na prévia do painel (destinations/admin.py)."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from destinations.admin import aviso_resolucao


def _foto(largura, altura):
    buf = io.BytesIO()
    Image.new('RGB', (largura, altura), '#3a6').save(buf, 'JPEG')
    return SimpleUploadedFile('f.jpg', buf.getvalue(), content_type='image/jpeg')


class Arquivo:
    """Imita o FieldFile: o ImageField lê a largura e a altura do arquivo."""
    def __init__(self, largura, altura):
        img = Image.open(_foto(largura, altura))
        self.width, self.height = img.size

    def __bool__(self):
        return True


class AvisoResolucaoTests(SimpleTestCase):
    def test_foto_pequena_avisa(self):
        html = aviso_resolucao(Arquivo(1200, 630))
        self.assertIn('1200 × 630 px', html)
        self.assertIn('resolucao--pequena', html)
        self.assertIn('1600', html)

    def test_foto_boa_so_mostra_o_tamanho(self):
        html = aviso_resolucao(Arquivo(1920, 1080))
        self.assertIn('1920 × 1080 px', html)
        self.assertNotIn('pequena', html)

    def test_sem_foto_nada(self):
        self.assertEqual(aviso_resolucao(None), '')
