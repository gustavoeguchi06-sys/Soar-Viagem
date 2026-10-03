"""Fotos do Instagram no #ViajantesSoar e renovação do token (com o Instagram simulado)."""
import io
import json
import os
import subprocess
import sys
from datetime import timedelta
from unittest import mock
from urllib import error

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import instagram
from .models import TokenInstagram

TOKEN = 'IGAA-token-do-env'


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _json(dados):
    return _Resposta(json.dumps(dados).encode())


FOTOS = {'data': [
    {'id': '1', 'media_type': 'IMAGE', 'media_url': 'https://scontent.cdninstagram.com/a.jpg',
     'permalink': 'https://www.instagram.com/p/AAA/', 'caption': 'Fervedouro no Jalapão\n#viajantessoar'},
    {'id': '2', 'media_type': 'VIDEO', 'media_url': 'https://video.cdninstagram.com/b.mp4',
     'thumbnail_url': 'https://scontent.cdninstagram.com/b.jpg',
     'permalink': 'https://www.instagram.com/reel/BBB/'},
    {'id': '3', 'media_type': 'IMAGE'},  # sem imagem: fica de fora
]}


def _instagram(fotos=FOTOS, renovado='IGAA-token-novo', falha_renovar=False):
    """Simula as duas chamadas: buscar fotos e renovar o token."""
    def responder(endereco, timeout):
        if 'refresh_access_token' in endereco:
            if falha_renovar:
                raise error.HTTPError(endereco, 400, 'Bad Request', {},
                                      io.BytesIO(b'{"error": {"message": "token novo demais"}}'))
            return _json({'access_token': renovado, 'expires_in': 5184000})
        return _json(fotos)
    return mock.patch('destinations.instagram.http.urlopen', side_effect=responder)


@override_settings(INSTAGRAM_TOKEN=TOKEN)
class InstagramTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_sem_token_nao_chama_o_instagram(self):
        with override_settings(INSTAGRAM_TOKEN=''), _instagram() as chamada:
            self.assertEqual(instagram.ultimas_fotos(), [])
            resposta = self.client.get(reverse('destinations:home'))
        chamada.assert_not_called()
        self.assertContains(resposta, 'href="https://instagram.com/operadorasoar"')

    def test_pagina_inicial_mostra_as_fotos_do_instagram(self):
        with _instagram():
            resposta = self.client.get(reverse('destinations:home'))
        self.assertContains(resposta, 'src="https://scontent.cdninstagram.com/a.jpg"')
        self.assertContains(resposta, 'href="https://www.instagram.com/p/AAA/"')
        self.assertContains(resposta, 'aria-label="Fervedouro no Jalapão (Instagram da Soar)"')
        # vídeo entra pela capa, nunca pelo mp4
        self.assertContains(resposta, 'src="https://scontent.cdninstagram.com/b.jpg"')
        self.assertNotContains(resposta, 'b.mp4')

    def test_busca_uma_vez_por_hora(self):
        with _instagram() as chamada:
            instagram.ultimas_fotos()
            instagram.ultimas_fotos()
        buscas = [c for c in chamada.call_args_list if 'me/media' in c.args[0]]
        self.assertEqual(len(buscas), 1)

    def test_instagram_fora_do_ar_nao_quebra_a_pagina(self):
        with mock.patch('destinations.instagram.http.urlopen',
                        side_effect=error.URLError('sem rede')):
            self.assertEqual(instagram.ultimas_fotos(), [])
            resposta = self.client.get(reverse('destinations:home'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'href="https://instagram.com/operadorasoar"')

    def test_renova_e_passa_a_usar_o_token_novo(self):
        with _instagram() as chamada:
            instagram.ultimas_fotos()
        salvo = TokenInstagram.objects.get()
        self.assertEqual(salvo.token, 'IGAA-token-novo')
        self.assertEqual(instagram.token_atual(), 'IGAA-token-novo')
        self.assertGreater(salvo.expira_em, timezone.now() + timedelta(days=59))
        self.assertIn('access_token=IGAA-token-novo', chamada.call_args_list[-1].args[0])

    def test_renovacao_recusada_segue_com_o_token_do_env(self):
        with _instagram(falha_renovar=True) as chamada:
            self.assertEqual(len(instagram.ultimas_fotos()), 2)
            cache.delete(instagram.CHAVE_FOTOS)
            instagram.ultimas_fotos()
        self.assertFalse(TokenInstagram.objects.exists())
        renovacoes = [c for c in chamada.call_args_list if 'refresh' in c.args[0]]
        self.assertEqual(len(renovacoes), 1)  # não insiste a cada busca

    def test_nao_renova_antes_de_7_dias(self):
        TokenInstagram.objects.create(token='IGAA-salvo', origem=instagram._impressao(TOKEN),
                                      renovado_em=timezone.now() - timedelta(days=2))
        self.assertFalse(instagram.precisa_renovar())
        with _instagram() as chamada:
            instagram.ultimas_fotos()
        self.assertTrue(all('refresh' not in c.args[0] for c in chamada.call_args_list))
        self.assertIn('access_token=IGAA-salvo', chamada.call_args_list[0].args[0])

    def test_token_novo_no_env_passa_na_frente_do_salvo(self):
        TokenInstagram.objects.create(token='IGAA-de-outro-token', origem='x' * 64,
                                      renovado_em=timezone.now())
        self.assertEqual(instagram.token_atual(), TOKEN)

    def test_comando_de_renovar(self):
        saida = io.StringIO()
        with _instagram():
            call_command('renovar_token_instagram', stdout=saida)
        self.assertIn('renovado', saida.getvalue())
        with _instagram(falha_renovar=True), self.assertRaisesMessage(CommandError, 'token novo demais'):
            call_command('renovar_token_instagram', '--forcar', stdout=io.StringIO())


class CspInstagramTests(TestCase):
    """O settings é lido de novo num processo separado, com e sem o token."""

    def _img_src(self, token):
        ambiente = {**os.environ, 'SOAR_DEBUG': '1', 'SOAR_INSTAGRAM_TOKEN': token}
        codigo = ('import os; os.environ["DJANGO_SETTINGS_MODULE"]="soar.settings"; '
                  'from django.conf import settings as s; print(s.CSP_DIRETIVAS["img-src"])')
        return subprocess.run([sys.executable, '-c', codigo], cwd=settings.BASE_DIR,
                              env=ambiente, capture_output=True, text=True).stdout

    def test_libera_as_fotos_do_instagram_so_com_token(self):
        self.assertIn('https://*.cdninstagram.com https://*.fbcdn.net', self._img_src(TOKEN))
        self.assertNotIn('cdninstagram', self._img_src(''))
