"""Testes das correções do diagnóstico de segurança e LGPD (22/09/2026).

Cada classe prende um achado: se alguém desfizer a correção, o teste quebra.

    python manage.py test
"""
from datetime import timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from contas.models import PerfilAgente
from contas.tokens import token_ativacao

from destinations.models import Destino
from reviews.models import Avaliacao

GOOGLE = override_settings(GOOGLE_CLIENT_ID='id-de-teste', GOOGLE_CLIENT_SECRET='segredo-de-teste')


def _virar_agencia(usuario, cnpj='11222333000181'):
    """Só agência e equipe têm login: os testes de conta usam uma agência."""
    PerfilAgente.objects.create(usuario=usuario, razao_social='Agência Teste', cnpj=cnpj,
                                cadastur='123', whatsapp='11999990000', aprovado=True)
    return usuario


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
        intruso = _virar_agencia(User.objects.create_user(
            'intruso', 'vitima@gmail.com', 'senha-do-intruso-123', is_active=False))

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
        dona = _virar_agencia(User.objects.create_user('dona', 'dona@gmail.com',
                                                       'senha-da-dona-123'))
        self._entrar_pelo_google('dona@gmail.com')
        dona.refresh_from_db()
        self.assertTrue(dona.check_password('senha-da-dona-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), dona.pk)

    def test_google_nao_cria_conta_nem_deixa_cliente_entrar(self):
        self._entrar_pelo_google('novo@gmail.com')
        self.assertFalse(User.objects.filter(email='novo@gmail.com').exists())
        User.objects.create_user('cliente', 'cliente@gmail.com', 'senha-do-cliente-123')
        self._entrar_pelo_google('cliente@gmail.com')
        self.assertNotIn('_auth_user_id', self.client.session)

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
            'token': token_ativacao.make_token(usuario),
        })

        resposta = self.client.get(link)

        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertRedirects(resposta, reverse('contas:entrar') + '?usuario=novo')
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
    """N9 — excluir a conta da agência leva junto o cadastro e os orçamentos dela."""

    def test_agencia_apaga_conta_perfil_e_orcamentos(self):
        from agencia.models import Orcamento
        usuario = User.objects.create_user('agencia', 'ag@exemplo.com', 'senha-boa-123')
        agente = PerfilAgente.objects.create(usuario=usuario, razao_social='Alfa Turismo',
                                             cnpj='11222333000181', cadastur='123',
                                             whatsapp='(11) 98888-7777', aprovado=True)
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        Orcamento.objects.create(agencia=agente, destino=destino, cliente_nome='Ana',
                                 cliente_telefone='11999999999')
        self.client.force_login(usuario)

        self.client.post(reverse('contas:excluir_conta'),
                         {'senha': 'senha-boa-123', 'confirmacao': 'on'})

        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(PerfilAgente.objects.exists())
        self.assertFalse(Orcamento.objects.exists())

    def test_meus_dados_traz_a_agencia_e_os_orcamentos(self):
        from agencia.models import Orcamento
        usuario = User.objects.create_user('agencia', 'ag@exemplo.com', 'senha-boa-123')
        agente = PerfilAgente.objects.create(usuario=usuario, razao_social='Alfa Turismo',
                                             cnpj='11222333000181', cadastur='123',
                                             whatsapp='(11) 98888-7777', aprovado=True)
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        Orcamento.objects.create(agencia=agente, destino=destino, cliente_nome='Ana')
        self.client.force_login(usuario)

        dados = self.client.get(reverse('contas:meus_dados')).json()
        self.assertEqual(dados['agencia']['razao_social'], 'Alfa Turismo')
        self.assertEqual([o['cliente'] for o in dados['orcamentos']], ['Ana'])
        self.assertNotIn('reservas', dados)


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

        from agencia.models import Orcamento
        agente = PerfilAgente.objects.create(usuario=cliente, razao_social='Alfa Turismo',
                                             cnpj='11222333000181', cadastur='123',
                                             whatsapp='(11) 98888-7777', aprovado=True)
        velho = Orcamento.objects.create(agencia=agente, destino=self.destino,
                                         cliente_nome='A', status='aceito')
        novo = Orcamento.objects.create(agencia=agente, destino=self.destino,
                                        cliente_nome='B', status='aceito')
        Orcamento.objects.filter(pk=velho.pk).update(
            atualizado_em=self.agora - timedelta(days=7 * 365))

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
        self.assertFalse(Orcamento.objects.filter(pk=velho.pk).exists())   # aceito há 7 anos
        self.assertTrue(Orcamento.objects.filter(pk=novo.pk).exists())
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


class ConfirmacaoComOutraContaAbertaTests(TestCase):
    """O dono testando o cadastro no mesmo navegador: o link não pode levar
    para o painel dele, e sim para entrar com a conta nova."""

    def test_link_sai_da_outra_conta_e_preenche_o_usuario(self):
        dono = User.objects.create_user('dono_x', 'dono@x.com', 'senha-boa-123', is_staff=True)
        novo = User.objects.create_user('karl_x', 'karl@x.com', 'senha-boa-123', is_active=False)
        self.client.force_login(dono)
        uid = urlsafe_base64_encode(force_bytes(novo.pk))
        token = token_ativacao.make_token(novo)
        resposta = self.client.get(reverse('contas:ativar', args=[uid, token]))
        self.assertTrue(User.objects.get(pk=novo.pk).is_active)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertIn('usuario=karl_x', resposta.url)
        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, 'value="karl_x"')


class MascarasTests(TestCase):
    """Telefone, CNPJ e CADASTUR chegam formatados mesmo sem o JavaScript."""

    def test_formatos(self):
        from django.core.exceptions import ValidationError
        from soar.mascaras import formatar_cadastur, formatar_telefone
        self.assertEqual(formatar_telefone('11988887777'), '(11) 98888-7777')
        self.assertEqual(formatar_telefone('+55 11 3333-4444'), '(11) 3333-4444')
        self.assertEqual(formatar_telefone(''), '')
        with self.assertRaises(ValidationError):
            formatar_telefone('98888777')
        self.assertEqual(formatar_cadastur('351234561000013'), '35.123456.10.0001-3')
        with self.assertRaises(ValidationError):
            formatar_cadastur('12345')

    def test_cadastro_de_agencia_grava_formatado(self):
        from contas.models import PerfilAgente
        resposta = self.client.post(reverse('contas:cadastro_agente'), {
            'first_name': 'Ana', 'email': 'ana@agencia.com', 'username': 'ana_ag',
            'password1': 'Senha-forte-123', 'password2': 'Senha-forte-123',
            'razao_social': 'Ana Turismo', 'cnpj': '11222333000181',
            'cadastur': '351234561000013', 'whatsapp': '11988887777',
            'aceite_privacidade': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        agencia = PerfilAgente.objects.get()
        self.assertEqual(agencia.cnpj, '11222333000181')
        self.assertEqual(agencia.cadastur, '35.123456.10.0001-3')
        self.assertEqual(agencia.whatsapp, '(11) 98888-7777')


class SoAgenciaEEquipeEntramTests(TestCase):
    """Cliente pessoa física não tem mais login: só agências e a equipe da Soar."""

    def test_cliente_nao_entra_nem_pela_tela_de_entrar_nem_pelo_b2b(self):
        User.objects.create_user('cliente', 'c@x.com', 'senha-boa-123')
        for tela in ('contas:entrar', 'contas:b2b'):
            resposta = self.client.post(reverse(tela), {'username': 'cliente',
                                                        'password': 'senha-boa-123'})
            self.assertContains(resposta, 'exclusivo das agências parceiras')
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_agencia_e_equipe_entram(self):
        _virar_agencia(User.objects.create_user('agencia', 'a@x.com', 'senha-boa-123'))
        User.objects.create_user('tuca', 't@x.com', 'senha-boa-123', is_staff=True)
        for nome in ('agencia', 'tuca'):
            self.client.post(reverse('contas:entrar'), {'username': nome,
                                                        'password': 'senha-boa-123'})
            self.assertEqual(self.client.session['_auth_user_id'],
                             str(User.objects.get(username=nome).pk))
            self.client.post(reverse('contas:sair'))

    def test_site_sem_cadastro_nem_botao_de_entrar(self):
        self.assertEqual(self.client.get('/cadastro/').status_code, 404)
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        for pagina in ('/', destino.get_absolute_url()):
            resposta = self.client.get(pagina)
            self.assertNotContains(resposta, reverse('contas:entrar'))
            self.assertNotContains(resposta, 'Criar conta')
            self.assertNotContains(resposta, 'Deixe sua avaliação')


class SiteEmConstrucaoTests(TestCase):
    """Tela "Site em Construção" (settings.SITE_EM_CONSTRUCAO): todos veem, menos o dono."""

    TITULO = 'Site em Construção'

    @override_settings(SITE_EM_CONSTRUCAO=False)
    def test_desligada_nao_aparece(self):
        self.assertNotContains(self.client.get('/'), self.TITULO)

    @override_settings(SITE_EM_CONSTRUCAO=True)
    def test_ligada_aparece_para_visitante_e_agencia_com_o_botao_das_reservas(self):
        resposta = self.client.get('/')
        self.assertContains(resposta, self.TITULO)
        self.assertContains(resposta, 'href="http://www.reservassoar.com.br/login"')
        agente = User.objects.create_user('agente', 'a@x.com', 'senha-boa-123')
        self.client.force_login(agente)
        self.assertContains(self.client.get('/blog/'), self.TITULO)

    @override_settings(SITE_EM_CONSTRUCAO=True, SITE_EM_CONSTRUCAO_ACESSO='codigo-secreto')
    def test_login_so_aparece_pelo_link_secreto(self):
        entrar = reverse('contas:entrar')
        self.assertContains(self.client.get(entrar), self.TITULO)
        self.assertContains(self.client.get(entrar, {'acesso': 'chute'}), self.TITULO)
        self.assertNotContains(self.client.get(entrar, {'acesso': 'codigo-secreto'}), self.TITULO)
        # o código só abre o login, não o resto do site
        self.assertContains(self.client.get('/', {'acesso': 'codigo-secreto'}), self.TITULO)

    @override_settings(SITE_EM_CONSTRUCAO=True, SITE_EM_CONSTRUCAO_ACESSO='')
    def test_sem_codigo_configurado_o_login_fica_coberto(self):
        self.assertContains(self.client.get(reverse('contas:entrar'), {'acesso': ''}), self.TITULO)

    @override_settings(SITE_EM_CONSTRUCAO=True)
    def test_ligada_o_dono_nao_ve(self):
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        self.assertNotContains(self.client.get('/'), self.TITULO)
