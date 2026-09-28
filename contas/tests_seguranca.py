"""Testes das correções da revisão de segurança de 28/09/2026.

Cada classe prova uma falha que existia e não existe mais:
- link de ativação que também trocava a senha;
- limite de login que zerava o IP quando alguém acertava a própria senha;
- "esqueci minha senha" e newsletter sem limite de envio;
- newsletter sem confirmação do dono do e-mail;
- envio grande lido inteiro antes de ser recusado;
- painel do dono protegido só por senha (agora pede o código do celular);
- redirecionamento aberto no login do painel.
"""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail, signing
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from blog.models import Inscricao
from blog.views import SAL_NEWSLETTER

from . import totp
from .models import DoisFatores
from .tokens import token_ativacao

SENHA = 'SenhaForte!2026'


class Base(TestCase):
    def setUp(self):
        cache.clear()


class TokenDeAtivacaoTests(Base):
    def _link(self, usuario):
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        return uid, token_ativacao.make_token(usuario)

    def test_link_de_ativacao_nao_troca_a_senha(self):
        usuario = User.objects.create_user('vitima', 'v@x.com', SENHA, is_active=False)
        uid, token = self._link(usuario)
        self.client.get(reverse('contas:ativar', args=[uid, token]))

        resposta = self.client.get(
            reverse('contas:password_reset_confirm', args=[uid, token]), follow=True)
        self.assertFalse(resposta.context['validlink'])
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password(SENHA))

    def test_link_de_ativacao_morre_depois_de_usado(self):
        usuario = User.objects.create_user('novo', 'n@x.com', SENHA, is_active=False)
        uid, token = self._link(usuario)
        self.client.get(reverse('contas:ativar', args=[uid, token]))
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertFalse(token_ativacao.check_token(usuario, token))


class ForcaBrutaTests(Base):
    def test_entrar_na_propria_conta_nao_zera_o_limite_do_ip(self):
        User.objects.create_user('meu', 'm@x.com', SENHA)
        for rodada in range(2):
            for i in range(3):
                self.client.post(reverse('contas:entrar'),
                                 {'username': 'alvo{}{}'.format(rodada, i), 'password': 'x'})
            self.client.post(reverse('contas:entrar'), {'username': 'meu', 'password': SENHA})
            self.client.post(reverse('contas:sair'))
        resposta = self.client.post(reverse('contas:entrar'),
                                    {'username': 'outro', 'password': 'x'})
        self.assertContains(resposta, 'Muitas tentativas')

    def test_acertar_a_senha_zera_so_a_contagem_da_conta(self):
        User.objects.create_user('ana', 'a@x.com', SENHA)
        for _ in range(3):
            self.client.post(reverse('contas:entrar'), {'username': 'ana', 'password': 'x'})
        self.client.post(reverse('contas:entrar'), {'username': 'ana', 'password': SENHA})
        self.assertIsNone(cache.get('limite:login:id:ana'))
        self.assertEqual(cache.get('limite:login:ip:127.0.0.1'), 3)


@override_settings(LIMITE_SENHA_POR_HORA=5)
class PedidoDeSenhaTests(Base):
    def test_pedidos_de_nova_senha_tem_limite(self):
        User.objects.create_user('a', 'a@x.com', SENHA)
        for _ in range(30):
            resposta = self.client.post(reverse('contas:senha_reset'), {'email': 'a@x.com'})
        self.assertEqual(len(mail.outbox), 5)
        self.assertContains(resposta, 'Muitos pedidos de nova senha')

    def test_limite_vale_tambem_para_email_sem_conta(self):
        for _ in range(6):
            resposta = self.client.post(reverse('contas:senha_reset'), {'email': 'ninguem@x.com'})
        self.assertContains(resposta, 'Muitos pedidos de nova senha')


class NewsletterTests(Base):
    def _inscrever(self, email='leitor@x.com'):
        return self.client.post(reverse('blog:inscrever'), {'email': email, 'voltar': '/blog/'},
                                follow=True)

    def _link_do_email(self):
        corpo = mail.outbox[-1].body
        return next(linha.strip() for linha in corpo.splitlines() if '/novidades/confirmar/' in linha)

    def test_inscricao_so_vale_depois_do_link(self):
        self._inscrever()
        inscricao = Inscricao.objects.get(email='leitor@x.com')
        self.assertFalse(inscricao.confirmada)
        self.assertEqual(len(mail.outbox), 1)

        self.client.get(self._link_do_email())
        inscricao.refresh_from_db()
        self.assertTrue(inscricao.confirmada)

    def test_link_falso_ou_vencido_nao_confirma(self):
        self._inscrever()
        resposta = self.client.get(reverse('blog:confirmar', args=['abc:def']), follow=True)
        self.assertContains(resposta, 'inválido ou expirou')

        token = signing.dumps('leitor@x.com', salt=SAL_NEWSLETTER)
        daqui_8_dias = timezone.now() + timedelta(days=8)
        with mock.patch('django.core.signing.time.time', return_value=daqui_8_dias.timestamp()):
            self.client.get(reverse('blog:confirmar', args=[token]))
        self.assertFalse(Inscricao.objects.get(email='leitor@x.com').confirmada)

    def test_tela_nao_conta_quem_ja_esta_inscrito(self):
        Inscricao.objects.create(email='ja@x.com', confirmada_em=timezone.now())
        ja = self._inscrever('ja@x.com')
        novo = self._inscrever('novo@x.com')
        self.assertEqual([str(m) for m in ja.context['messages']][0].replace('ja@x.com', 'E'),
                         [str(m) for m in novo.context['messages']][0].replace('novo@x.com', 'E'))
        self.assertEqual(len(mail.outbox), 1)      # quem já confirmou não recebe de novo

    @override_settings(LIMITE_NEWSLETTER_POR_HORA=5)
    def test_newsletter_tem_limite(self):
        for i in range(20):
            self._inscrever('x{}@x.com'.format(i))
        self.assertEqual(Inscricao.objects.count(), 5)
        self.assertEqual(len(mail.outbox), 5)

    def test_expurgo_apaga_inscricao_nunca_confirmada(self):
        velha = Inscricao.objects.create(email='velha@x.com')
        Inscricao.objects.filter(pk=velha.pk).update(criado_em=timezone.now() - timedelta(days=8))
        Inscricao.objects.create(email='recente@x.com')
        Inscricao.objects.create(email='ok@x.com', confirmada_em=timezone.now() - timedelta(days=90))
        call_command('expurgar_dados', stdout=StringIO())
        self.assertEqual(set(Inscricao.objects.values_list('email', flat=True)),
                         {'recente@x.com', 'ok@x.com'})


class LimiteDeEnvioTests(Base):
    @override_settings(TAMANHO_MAXIMO_ENVIO=1024)
    def test_envio_grande_e_recusado_antes_de_ser_lido(self):
        with mock.patch('django.core.handlers.wsgi.WSGIRequest._load_post_and_files') as leitura:
            resposta = self.client.post(reverse('contas:entrar'), {'username': 'a' * 5000})
        self.assertEqual(resposta.status_code, 413)
        leitura.assert_not_called()

    def test_envio_normal_passa(self):
        resposta = self.client.post(reverse('contas:entrar'), {'username': 'a', 'password': 'b'})
        self.assertEqual(resposta.status_code, 200)


@override_settings(DOIS_FATORES_EQUIPE=True)
class DoisFatoresTests(Base):
    def setUp(self):
        super().setUp()
        self.dono = User.objects.create_superuser('dono', 'd@x.com', SENHA)
        self.painel = reverse('admin:index')

    def _entrar(self):
        self.client.post(reverse('contas:entrar'), {'username': 'dono', 'password': SENHA})

    def _codigo(self, segredo, passo_extra=0):
        return totp.codigo(segredo, totp.passo_atual() + passo_extra)

    def test_senha_sozinha_nao_abre_o_painel(self):
        self._entrar()
        resposta = self.client.get(self.painel, follow=True)
        self.assertEqual(resposta.redirect_chain[-1][0].split('?')[0],
                         reverse('contas:dois_fatores'))
        self.assertContains(resposta, 'Proteja o painel com o celular')

    def test_cadastrar_o_celular_libera_o_painel(self):
        self._entrar()
        self.client.get(reverse('contas:dois_fatores'))
        segredo = self.client.session['soar_2fa_novo_segredo']
        self.client.post(reverse('contas:dois_fatores'), {'codigo': self._codigo(segredo)})
        self.assertTrue(DoisFatores.objects.filter(usuario=self.dono).exists())
        self.assertEqual(self.client.get(self.painel).status_code, 200)

    def test_nova_sessao_pede_o_codigo_de_novo(self):
        segredo = totp.novo_segredo()
        DoisFatores.objects.create(usuario=self.dono, segredo=segredo)
        self._entrar()
        self.assertEqual(self.client.get(self.painel).status_code, 302)

        errado = self.client.post(reverse('contas:dois_fatores'), {'codigo': '000000'})
        self.assertContains(errado, 'Código não confere')
        self.assertEqual(self.client.get(self.painel).status_code, 302)

        self.client.post(reverse('contas:dois_fatores'), {'codigo': self._codigo(segredo)})
        self.assertEqual(self.client.get(self.painel).status_code, 200)

    def test_mesmo_codigo_nao_entra_duas_vezes(self):
        segredo = totp.novo_segredo()
        DoisFatores.objects.create(usuario=self.dono, segredo=segredo)
        codigo = self._codigo(segredo)
        self._entrar()
        self.client.post(reverse('contas:dois_fatores'), {'codigo': codigo})
        self.client.post(reverse('contas:sair'))

        self._entrar()
        resposta = self.client.post(reverse('contas:dois_fatores'), {'codigo': codigo})
        self.assertContains(resposta, 'Código não confere')

    def test_chute_do_codigo_tem_limite(self):
        segredo = totp.novo_segredo()
        DoisFatores.objects.create(usuario=self.dono, segredo=segredo)
        self._entrar()
        for _ in range(5):
            self.client.post(reverse('contas:dois_fatores'), {'codigo': '000000'})
        resposta = self.client.post(reverse('contas:dois_fatores'), {'codigo': self._codigo(segredo)})
        self.assertContains(resposta, 'Muitos códigos errados')
        self.assertEqual(self.client.get(self.painel).status_code, 302)

    def test_cliente_nao_e_afetado(self):
        User.objects.create_user('cliente', 'c@x.com', SENHA)
        self.client.post(reverse('contas:entrar'), {'username': 'cliente', 'password': SENHA})
        resposta = self.client.get(reverse('contas:dois_fatores'))
        self.assertRedirects(resposta, reverse('contas:minha_conta'))

    def test_comando_desliga_para_quem_perdeu_o_celular(self):
        DoisFatores.objects.create(usuario=self.dono, segredo=totp.novo_segredo())
        call_command('desligar_dois_fatores', 'dono', stdout=StringIO())
        self.assertFalse(DoisFatores.objects.filter(usuario=self.dono).exists())

    def test_login_do_painel_nao_redireciona_para_fora(self):
        segredo = totp.novo_segredo()
        DoisFatores.objects.create(usuario=self.dono, segredo=segredo)
        self._entrar()
        self.client.post(reverse('contas:dois_fatores'), {'codigo': self._codigo(segredo)})
        resposta = self.client.get(reverse('admin:login') + '?next=https://golpe.example/')
        self.assertEqual(resposta['Location'], self.painel)


class CodigoTotpTests(TestCase):
    def test_vetores_da_rfc_6238(self):
        import base64
        segredo = base64.b32encode(b'12345678901234567890').decode()
        self.assertEqual(totp.codigo(segredo, 59 // 30), '287082')
        self.assertEqual(totp.codigo(segredo, 1111111109 // 30), '081804')
        self.assertEqual(totp.codigo(segredo, 2000000000 // 30), '279037')


class TravaDeEnvioTests(TestCase):
    def test_script_que_trava_o_botao_esta_em_todas_as_paginas(self):
        resposta = self.client.get(reverse('destinations:home'))
        self.assertContains(resposta, 'js/envio.js')


class CspTests(TestCase):
    def test_csp_bloqueia_por_padrao(self):
        resposta = self.client.get(reverse('destinations:home'))
        self.assertIn("script-src 'self'", resposta['Content-Security-Policy'])
        self.assertNotIn('Content-Security-Policy-Report-Only', resposta)
