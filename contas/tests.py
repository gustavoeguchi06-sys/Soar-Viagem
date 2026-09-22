"""Testes das correções do diagnóstico de segurança e LGPD (22/09/2026).

Cada classe prende um achado: se alguém desfizer a correção, o teste quebra.

    python manage.py test
"""
from datetime import timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from destinations.models import Destino
from reservas.models import Reserva
from reviews.models import Avaliacao

GOOGLE = override_settings(GOOGLE_CLIENT_ID='id-de-teste', GOOGLE_CLIENT_SECRET='segredo-de-teste')


def _respostas_google(email, verificado=True, nome='Ana'):
    """O que o Google devolveria: primeiro o token, depois o perfil."""
    return [
        {'access_token': 'token-de-teste'},
        {'email': email, 'email_verified': verificado, 'given_name': nome},
    ]


@GOOGLE
class LoginGoogleTests(TestCase):
    """N1 — o login com Google não pode herdar a senha de uma conta pré-cadastrada."""

    def _entrar_pelo_google(self, email, **kwargs):
        inicio = self.client.get(reverse('contas:google_iniciar'))
        state = parse_qs(urlparse(inicio['Location']).query)['state'][0]
        with mock.patch('contas.google._post_json',
                        side_effect=_respostas_google(email, **kwargs)):
            return self.client.get(reverse('contas:google_retorno'),
                                   {'state': state, 'code': 'codigo-de-teste'})

    def test_conta_pre_cadastrada_perde_a_senha_do_intruso(self):
        # alguém cadastrou o e-mail da vítima com uma senha só dele e nunca confirmou
        intruso = User.objects.create_user('intruso', 'vitima@gmail.com', 'senha-do-intruso-123',
                                           is_active=False)

        self._entrar_pelo_google('vitima@gmail.com')

        intruso.refresh_from_db()
        self.assertTrue(intruso.is_active)                        # a dona de verdade entrou
        self.assertFalse(intruso.has_usable_password())           # e a senha antiga morreu
        self.assertFalse(intruso.check_password('senha-do-intruso-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), intruso.pk)

        # e o intruso não entra mais pela porta de senha
        self.client.logout()
        self.client.post(reverse('contas:entrar'),
                         {'username': 'intruso', 'password': 'senha-do-intruso-123'})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_conta_ja_ativa_mantem_a_senha(self):
        # quem já confirmou o e-mail escolheu a senha — ela é da própria pessoa
        dona = User.objects.create_user('dona', 'dona@gmail.com', 'senha-da-dona-123')
        self._entrar_pelo_google('dona@gmail.com')
        dona.refresh_from_db()
        self.assertTrue(dona.check_password('senha-da-dona-123'))

    def test_conta_desativada_no_painel_nao_volta_pelo_google(self):
        banida = User.objects.create_user('banida', 'banida@gmail.com', 'x-senha-123',
                                          is_active=False)
        banida.last_login = timezone.now() - timedelta(days=90)   # já usou o site antes
        banida.save()

        self._entrar_pelo_google('banida@gmail.com')

        banida.refresh_from_db()
        self.assertFalse(banida.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_email_nao_verificado_no_google_e_recusado(self):
        self._entrar_pelo_google('novo@gmail.com', verificado=False)
        self.assertFalse(User.objects.filter(email='novo@gmail.com').exists())

    def test_state_errado_e_recusado(self):
        self.client.get(reverse('contas:google_iniciar'))
        with mock.patch('contas.google._post_json') as falar_com_google:
            self.client.get(reverse('contas:google_retorno'),
                            {'state': 'forjado', 'code': 'codigo'})
        falar_com_google.assert_not_called()
        self.assertNotIn('_auth_user_id', self.client.session)


class ConfirmacaoDeEmailTests(TestCase):
    """N2 — o link de confirmação liga a conta, mas não entra nela."""

    def test_link_ativa_sem_fazer_login(self):
        usuario = User.objects.create_user('novo', 'novo@exemplo.com', 'senha-boa-123',
                                           is_active=False)
        link = reverse('contas:ativar', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(usuario.pk)),
            'token': default_token_generator.make_token(usuario),
        })

        resposta = self.client.get(link)

        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertRedirects(resposta, reverse('contas:entrar'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_link_adulterado_nao_ativa(self):
        usuario = User.objects.create_user('novo2', 'novo2@exemplo.com', 'senha-boa-123',
                                           is_active=False)
        link = reverse('contas:ativar', kwargs={
            'uidb64': urlsafe_base64_encode(force_bytes(usuario.pk)), 'token': 'abc-123'})
        self.assertEqual(self.client.get(link).status_code, 400)
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)


class ExclusaoDeContaTests(TestCase):
    """N9 — excluir a conta anonimiza as reservas em vez de apagá-las."""

    def test_reserva_fica_sem_dados_pessoais(self):
        usuario = User.objects.create_user('cliente', 'cliente@exemplo.com', 'senha-boa-123')
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        reserva = Reserva.objects.create(usuario=usuario, destino=destino,
                                         telefone='11999999999', observacao='sou alérgica a camarão')
        self.client.force_login(usuario)

        self.client.post(reverse('contas:excluir_conta'),
                         {'senha': 'senha-boa-123', 'confirmacao': 'on'})

        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())
        reserva.refresh_from_db()                                 # a reserva continua...
        self.assertIsNone(reserva.usuario)                        # ...sem dono,
        self.assertEqual(reserva.telefone, '')                    # sem telefone
        self.assertNotIn('camarão', reserva.observacao)           # e sem a observação


class ExpurgoTests(TestCase):
    """N5 e N7 — o que o aviso de privacidade promete apagar, é apagado."""

    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.agora = timezone.now()

    def _usuario(self, nome, dias, ativo=False, ja_entrou=False):
        u = User.objects.create_user(nome, nome + '@exemplo.com', 'senha-boa-123', is_active=ativo)
        User.objects.filter(pk=u.pk).update(
            date_joined=self.agora - timedelta(days=dias),
            last_login=self.agora - timedelta(days=1) if ja_entrou else None)
        return u

    def test_apaga_so_o_que_venceu(self):
        abandonada = self._usuario('abandonada', dias=40)
        recente = self._usuario('recente', dias=10)
        desativada = self._usuario('desativada', dias=400, ja_entrou=True)
        cliente = self._usuario('cliente', dias=3000, ativo=True, ja_entrou=True)

        velha = Reserva.objects.create(usuario=cliente, destino=self.destino)
        nova = Reserva.objects.create(usuario=cliente, destino=self.destino)
        Reserva.objects.filter(pk=velha.pk).update(criado_em=self.agora - timedelta(days=7 * 365))

        antiga = Avaliacao.objects.create(destino=self.destino, autor=cliente, nome_autor='C',
                                          comentario='Muito bom mesmo.', ip='200.1.2.3')
        Avaliacao.objects.filter(pk=antiga.pk).update(criado_em=self.agora - timedelta(days=200))
        outro = self._usuario('outro', dias=500, ativo=True, ja_entrou=True)
        fresca = Avaliacao.objects.create(destino=self.destino, autor=outro, nome_autor='O',
                                          comentario='Voltaria amanhã.', ip='200.1.2.4')

        call_command('expurgar_dados', stdout=mock.MagicMock())

        existe = lambda u: User.objects.filter(pk=u.pk).exists()
        self.assertFalse(existe(abandonada))       # 40 dias sem confirmar: sai
        self.assertTrue(existe(recente))           # 10 dias: ainda tem prazo
        self.assertTrue(existe(desativada))        # desligada no painel: não é cadastro abandonado
        self.assertFalse(Reserva.objects.filter(pk=velha.pk).exists())
        self.assertTrue(Reserva.objects.filter(pk=nova.pk).exists())
        antiga.refresh_from_db()
        fresca.refresh_from_db()
        self.assertIsNone(antiga.ip)               # a avaliação fica, o IP não
        self.assertEqual(fresca.ip, '200.1.2.4')

    def test_simular_nao_apaga_nada(self):
        abandonada = self._usuario('abandonada', dias=40)
        call_command('expurgar_dados', '--simular', stdout=mock.MagicMock())
        self.assertTrue(User.objects.filter(pk=abandonada.pk).exists())


class PaginasSemTerceirosTests(TestCase):
    """N4 — abrir o site não chama servidor de fora."""

    def test_nenhuma_fonte_do_google(self):
        for nome in ('destinations:home', 'contas:entrar', 'contas:privacidade'):
            resposta = self.client.get(reverse(nome))
            self.assertEqual(resposta.status_code, 200)
            html = resposta.content.decode()
            self.assertNotIn('googleapis', html, nome)
            self.assertNotIn('gstatic', html, nome)
            self.assertIn('css/fontes.css', html, nome)
            csp = resposta.get('Content-Security-Policy') or resposta.get(
                'Content-Security-Policy-Report-Only')
            self.assertNotIn('google', csp)
