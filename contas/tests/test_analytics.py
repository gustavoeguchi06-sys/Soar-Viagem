"""Google Analytics com consentimento (static/js/analytics.js).

O que estes testes prendem:
- sem SOAR_GA_ID, o site fica exatamente como era: nada do Google, sem banner;
- com o ID, o HTML traz o banner e o analytics.js, mas nunca o script do Google
  direto na página (ele só é baixado no navegador, depois do "Aceitar");
- o dono/equipe não é contado;
- a CSP só libera os endereços do Google quando o GA está ligado;
- o aviso de privacidade acompanha.

    python manage.py test contas.tests.test_analytics
"""
import os
import subprocess
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

GA = override_settings(GA_ID='G-TESTE12345')


class SemAnalyticsTests(TestCase):
    def test_nada_do_google_nem_banner(self):
        for nome in ('destinations:home', 'contas:privacidade', 'blog:indice'):
            html = self.client.get(reverse(nome)).content.decode()
            self.assertNotIn('analytics.js', html, nome)
            self.assertNotIn('banner-cookies', html, nome)
            self.assertNotIn('googletagmanager', html, nome)
            self.assertNotIn('Preferências de cookies', html, nome)

    def test_aviso_de_privacidade_diz_que_nao_ha_analytics(self):
        html = self.client.get(reverse('contas:privacidade')).content.decode()
        self.assertIn('Não há cookie de', html)
        self.assertNotIn('só se você aceitar', html)


@GA
class ComAnalyticsTests(TestCase):
    def test_banner_e_script_com_o_id(self):
        html = self.client.get(reverse('destinations:home')).content.decode()
        self.assertIn('id="banner-cookies"', html)
        self.assertIn('data-ga="G-TESTE12345"', html)
        self.assertIn('css/cookies.css', html)
        self.assertIn('data-cookies-preferencias', html)

    def test_banner_comeca_escondido_e_com_os_dois_botoes(self):
        html = self.client.get(reverse('destinations:home')).content.decode()
        inicio = html.index('id="banner-cookies"')
        trecho = html[inicio - 80:html.index('</section>', inicio)]
        self.assertIn('hidden', trecho)
        self.assertIn('data-cookies="aceitar"', trecho)
        self.assertIn('data-cookies="recusar"', trecho)
        # o comentário do template não pode vazar para a página
        self.assertNotIn('Banner de cookies do Google Analytics', html)

    def test_google_nunca_vem_direto_no_html(self):
        # o gtag.js só pode entrar pelo analytics.js, depois do consentimento
        html = self.client.get(reverse('destinations:home')).content.decode()
        self.assertNotIn('googletagmanager.com/gtag', html)
        self.assertNotIn('gtag(', html)

    def test_equipe_nao_e_contada(self):
        dono = User.objects.create_user('dono_ga', 'dono@x.com', 'senha-boa-123', is_staff=True)
        self.client.force_login(dono)
        html = self.client.get(reverse('destinations:home')).content.decode()
        self.assertNotIn('analytics.js', html)
        self.assertNotIn('banner-cookies', html)

    def test_cliente_logado_ve_o_banner(self):
        cliente = User.objects.create_user('cliente_ga', 'c@x.com', 'senha-boa-123')
        self.client.force_login(cliente)
        html = self.client.get(reverse('destinations:home')).content.decode()
        self.assertIn('analytics.js', html)

    def test_aviso_de_privacidade_explica_o_analytics(self):
        html = self.client.get(reverse('contas:privacidade')).content.decode()
        self.assertIn('id="cookies"', html)
        self.assertIn('Google Analytics', html)
        self.assertIn('só se você aceitar', html)
        self.assertIn('data-cookies-preferencias', html)


class ConfiguracaoAnalyticsTests(TestCase):
    """O settings lido de novo num processo separado, com o SOAR_GA_ID."""

    def _settings_com(self, **variaveis):
        ambiente = {**os.environ, 'SOAR_DEBUG': '1', **variaveis}
        codigo = ('import django, os; os.environ["DJANGO_SETTINGS_MODULE"]="soar.settings"; '
                  'from django.conf import settings as s; print(s.GA_ID); '
                  'print(s.CSP_DIRETIVAS["script-src"]); print(s.CSP_DIRETIVAS["connect-src"])')
        return subprocess.run([sys.executable, '-c', codigo], cwd=settings.BASE_DIR,
                              env=ambiente, capture_output=True, text=True)

    def test_sem_id_a_csp_nao_tem_google(self):
        saida = self._settings_com(SOAR_GA_ID='').stdout
        self.assertNotIn('google', saida)

    def test_com_id_a_csp_libera_so_o_google_analytics(self):
        saida = self._settings_com(SOAR_GA_ID='g-ab12cd34ef').stdout
        self.assertIn('G-AB12CD34EF', saida)
        self.assertIn("'self' https://www.googletagmanager.com", saida)
        self.assertIn('https://*.google-analytics.com', saida)

    def test_id_errado_recusa_subir(self):
        resultado = self._settings_com(SOAR_GA_ID='UA-12345-1')
        self.assertIn('SOAR_GA_ID inválido', resultado.stderr)
