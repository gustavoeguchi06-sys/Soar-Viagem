"""Pop-up de aviso aos agentes: aparece só logo depois do login aprovado e fecha no X."""
import io
import shutil
import tempfile
import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from agencia.models import AvisoAgente
from contas.models import PerfilAgente

SENHA = 'senha-boa-123'
MEDIA = tempfile.mkdtemp()


def _png():
    buf = io.BytesIO()
    Image.new('RGB', (90, 160), '#f59a2f').save(buf, 'PNG')
    return SimpleUploadedFile('black.png', buf.getvalue(), content_type='image/png')


def _agente(login, aprovado=True):
    usuario = User.objects.create_user(login, login + '@agencia.com', SENHA, first_name=login)
    PerfilAgente.objects.create(usuario=usuario, razao_social='Alfa Turismo',
                                cnpj='11222333000181' if aprovado else '22333444000192',
                                whatsapp='11999990000', aprovado=aprovado)
    return usuario


@override_settings(MEDIA_ROOT=MEDIA)
class AvisoAgenteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.aviso = AvisoAgente.objects.create(titulo='Black do Agente', imagem=_png())
        self.painel = reverse('agencia:painel')

    def test_aparece_so_depois_do_login_pelo_b2b(self):
        _agente('ana')
        resposta = self.client.post(reverse('contas:b2b'),
                                    {'username': 'ana', 'password': SENHA}, follow=True)
        self.assertEqual(resposta.request['PATH_INFO'], self.painel)
        self.assertContains(resposta, 'id="avisoAgente"')
        self.assertContains(resposta, 'aria-label="Fechar aviso"')
        self.assertContains(resposta, self.aviso.imagem.url)
        # nas páginas seguintes não volta; só no próximo login
        self.assertNotContains(self.client.get(self.painel), 'id="avisoAgente"')
        self.assertNotContains(self.client.get(reverse('destinations:home')), 'id="avisoAgente"')
        self.client.logout()
        self.client.login(username='ana', password=SENHA)
        self.assertContains(self.client.get(self.painel), 'id="avisoAgente"')

    def test_pedido_que_nao_mostra_a_pagina_nao_gasta_o_aviso(self):
        # o navegador pede o ícone do site ou uma imagem que não existe logo
        # depois do login: isso não pode gastar o pop-up
        _agente('ana')
        self.client.login(username='ana', password=SENHA)
        self.client.get('/favicon-que-nao-existe.ico')
        self.assertContains(self.client.get(self.painel), 'id="avisoAgente"')

    def test_agente_que_ja_estava_logado_nao_ve(self):
        usuario = _agente('ana')
        AvisoAgente.objects.all().delete()
        self.client.force_login(usuario)
        self.client.get(self.painel)
        # o dono liga o aviso depois: só aparece no próximo login
        AvisoAgente.objects.create(titulo='Black', imagem=_png())
        self.assertNotContains(self.client.get(self.painel), 'id="avisoAgente"')

    def test_javascript_em_arquivo_por_causa_da_csp(self):
        # a CSP do site (script-src 'self') bloqueia <script> escrito na página:
        # foi por isso que o pop-up não abria na primeira versão
        _agente('ana')
        self.client.login(username='ana', password=SENHA)
        html = self.client.get(self.painel).content.decode()
        trecho = html[html.index('id="avisoAgente"'):]
        self.assertIn('js/aviso-agente.js', trecho)
        self.assertIsNone(re.search(r'<script(?![^>]*\bsrc=)[^>]*>', trecho))

    def test_cliente_e_agencia_nao_aprovada_nao_veem(self):
        User.objects.create_user('cliente', 'c@x.com', SENHA)
        self.client.login(username='cliente', password=SENHA)
        self.assertNotContains(self.client.get(reverse('destinations:home')), 'id="avisoAgente"')
        self.client.logout()
        _agente('bia', aprovado=False)
        self.client.login(username='bia', password=SENHA)
        self.assertNotContains(self.client.get(reverse('destinations:home')), 'id="avisoAgente"')

    def test_desligado_ou_vencido_nao_aparece(self):
        _agente('ana')
        self.aviso.ativo = False
        self.aviso.save()
        self.client.login(username='ana', password=SENHA)
        self.assertNotContains(self.client.get(self.painel), 'id="avisoAgente"')
        self.client.logout()
        self.aviso.ativo = True
        self.aviso.mostrar_ate = timezone.localdate() - timedelta(days=1)
        self.aviso.save()
        self.client.login(username='ana', password=SENHA)
        self.assertNotContains(self.client.get(self.painel), 'id="avisoAgente"')

    def test_ate_hoje_ainda_aparece(self):
        _agente('ana')
        self.aviso.mostrar_ate = timezone.localdate()
        self.aviso.save()
        self.client.login(username='ana', password=SENHA)
        self.assertContains(self.client.get(self.painel), 'id="avisoAgente"')
