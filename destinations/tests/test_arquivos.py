"""Arquivo sem uso sai do armazenamento; R2 liga só com todas as variáveis."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from ..models import Destino, ImagemDestino

PASTA = tempfile.mkdtemp()
GIF = b'GIF89a\x01\x00\x01\x00\x00\x00\x00;'


def _foto(nome='foto.gif'):
    return SimpleUploadedFile(nome, GIF, content_type='image/gif')


@override_settings(MEDIA_ROOT=PASTA)
class ArquivosSemUsoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA, ignore_errors=True)

    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')

    def _existe(self, nome):
        return (Path(PASTA) / nome).exists()

    def test_apagar_o_registro_apaga_o_arquivo(self):
        with self.captureOnCommitCallbacks(execute=True):
            imagem = ImagemDestino.objects.create(destino=self.destino, imagem=_foto())
        nome = imagem.imagem.name
        self.assertTrue(self._existe(nome))
        with self.captureOnCommitCallbacks(execute=True):
            imagem.delete()
        self.assertFalse(self._existe(nome))

    def test_trocar_a_foto_apaga_a_antiga(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.destino.imagem_capa = _foto('capa.gif')
            self.destino.save()
        antiga = self.destino.imagem_capa.name
        with self.captureOnCommitCallbacks(execute=True):
            self.destino.imagem_capa = _foto('nova.gif')
            self.destino.save()
        self.assertFalse(self._existe(antiga))
        self.assertTrue(self._existe(self.destino.imagem_capa.name))

    def test_nao_apaga_arquivo_que_outro_registro_usa(self):
        with self.captureOnCommitCallbacks(execute=True):
            primeira = ImagemDestino.objects.create(destino=self.destino, imagem=_foto())
        ImagemDestino.objects.create(destino=self.destino, imagem=primeira.imagem.name)
        with self.captureOnCommitCallbacks(execute=True):
            primeira.delete()
        self.assertTrue(self._existe(primeira.imagem.name))


class ConfiguracaoR2Tests(TestCase):
    """O settings é lido de novo num processo separado, com as variáveis do R2."""

    def _settings_com(self, **variaveis):
        ambiente = {**os.environ, 'SOAR_DEBUG': '1', **variaveis}
        codigo = ('import django, os; os.environ["DJANGO_SETTINGS_MODULE"]="soar.settings"; '
                  'from django.conf import settings as s; '
                  'print(s.STORAGES["default"]["BACKEND"]); print(s.MEDIA_URL); '
                  'print(s.CSP_DIRETIVAS["img-src"])')
        return subprocess.run([sys.executable, '-c', codigo], cwd=settings.BASE_DIR,
                              env=ambiente, capture_output=True, text=True)

    def test_sem_variaveis_fica_no_disco(self):
        self.assertNotIn('S3Storage', self._settings_com(SOAR_R2_BUCKET='').stdout)

    def test_com_variaveis_usa_o_r2(self):
        saida = self._settings_com(SOAR_R2_BUCKET='soar-midia', SOAR_R2_ACCOUNT_ID='abc',
                                   SOAR_R2_ACCESS_KEY='chave', SOAR_R2_SECRET_KEY='segredo',
                                   SOAR_R2_DOMINIO='midia.soar.com.br').stdout
        self.assertIn('storages.backends.s3.S3Storage', saida)
        self.assertIn('https://midia.soar.com.br/', saida)
        self.assertIn("'self' data: https://midia.soar.com.br", saida)

    def test_faltando_variavel_recusa_subir(self):
        resultado = self._settings_com(SOAR_R2_BUCKET='soar-midia', SOAR_R2_ACCOUNT_ID='',
                                       SOAR_R2_ACCESS_KEY='', SOAR_R2_SECRET_KEY='',
                                       SOAR_R2_DOMINIO='')
        self.assertIn('falta SOAR_R2_ACCOUNT_ID', resultado.stderr)


@override_settings(MEDIA_ROOT=PASTA)
class FotosDoPainelTests(TestCase):
    def test_so_aceita_foto_de_formato_e_tamanho_certos(self):
        from django.core.exceptions import ValidationError
        from soar.videos import validar_foto
        validar_foto(_foto('capa.jpg'))
        with self.assertRaisesMessage(ValidationError, 'JPG, PNG, WebP ou GIF'):
            validar_foto(_foto('capa.heic'))
        with self.assertRaisesMessage(ValidationError, 'JPG, PNG, WebP ou GIF'):
            validar_foto(_foto('capa.svg'))
        with override_settings(TAMANHO_MAXIMO_FOTO_PAINEL=5):
            with self.assertRaisesMessage(ValidationError, 'grande demais'):
                validar_foto(_foto('capa.jpg'))

    def test_foto_antiga_nao_impede_salvar_o_registro(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         imagem_capa='destinos/antiga.svg')
        destino.full_clean()        # não levanta: o arquivo já estava salvo


class ConsultasPorPaginaTests(TestCase):
    """Mais viagens no catálogo não pode virar mais consultas ao banco (N+1)."""

    def _consultas(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as q:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(q.captured_queries)

    def test_lista_de_viagens_nao_cresce_com_o_catalogo(self):
        for i in range(2):
            Destino.objects.create(nome='Viagem {}'.format(i), slug='v{}'.format(i), descricao='.')
        poucas = {url: self._consultas(url) for url in ('/destinos/', '/', '/soar-60/')}
        for i in range(2, 8):
            Destino.objects.create(nome='Viagem {}'.format(i), slug='v{}'.format(i), descricao='.')
        for url, antes in poucas.items():
            with self.subTest(url=url):
                self.assertEqual(self._consultas(url), antes)
