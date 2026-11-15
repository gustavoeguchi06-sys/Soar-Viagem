"""Link da viagem e do blog com foto no WhatsApp (soar/compartilhar.py)."""
import io
import re
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from blog.models import Artigo, Categoria
from destinations.models import Destino
from soar.compartilhar import primeira_foto

MEDIA = tempfile.mkdtemp()


def _jpg():
    buf = io.BytesIO()
    Image.new('RGB', (1200, 630), '#3a6').save(buf, 'JPEG')
    return SimpleUploadedFile('capa.jpg', buf.getvalue(), content_type='image/jpeg')


def _meta(html, nome):
    achado = re.search(r'<meta (?:property|name)="{}" content="([^"]*)"'.format(re.escape(nome)), html)
    return achado.group(1) if achado else None


@override_settings(MEDIA_ROOT=MEDIA)
class CompartilharTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_viagem_com_capa_vai_com_a_foto_grande(self):
        destino = Destino.objects.create(nome='Jalapão/TO', slug='jalapao', descricao='x',
                                         subtitulo='Dunas, fervedouros e cachoeiras',
                                         imagem_capa=_jpg())
        html = self.client.get(destino.get_absolute_url()).content.decode()
        self.assertEqual(_meta(html, 'og:title'), 'Jalapão/TO | Soar Operadora')
        self.assertEqual(_meta(html, 'og:description'), 'Dunas, fervedouros e cachoeiras')
        imagem = _meta(html, 'og:image')
        self.assertTrue(imagem.startswith('http://testserver/'), imagem)
        self.assertTrue(imagem.endswith('.jpg'), imagem)
        self.assertEqual(_meta(html, 'twitter:card'), 'summary_large_image')
        self.assertEqual(_meta(html, 'og:url'), 'http://testserver' + destino.get_absolute_url())

    def test_viagem_sem_foto_usa_o_logo_e_nao_a_ilustracao_svg(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='x')
        html = self.client.get(destino.get_absolute_url()).content.decode()
        self.assertTrue(_meta(html, 'og:image').endswith('.png'))
        self.assertEqual(_meta(html, 'twitter:card'), 'summary')

    def test_artigo_do_blog(self):
        cat = Categoria.objects.create(nome='Dicas', slug='dicas')
        artigo = Artigo.objects.create(titulo='Roteiro no Jalapão', slug='roteiro', categoria=cat,
                                       resumo='Cinco dias entre dunas.', publicado=True,
                                       capa=_jpg())
        html = self.client.get(artigo.get_absolute_url()).content.decode()
        self.assertEqual(_meta(html, 'og:title'), 'Roteiro no Jalapão')
        self.assertEqual(_meta(html, 'og:type'), 'article')
        self.assertTrue(_meta(html, 'og:image').endswith('.jpg'))

    def test_pagina_comum_tem_o_padrao(self):
        html = self.client.get('/').content.decode()
        self.assertIn('Soar Operadora', _meta(html, 'og:title'))
        self.assertIsNotNone(_meta(html, 'og:image'))

    def test_primeira_foto_pula_svg(self):
        self.assertEqual(primeira_foto('/static/img/dunas.svg', '/media/a.JPG'), '/media/a.JPG')
        self.assertEqual(primeira_foto('/static/img/dunas.svg'), '')
