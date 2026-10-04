"""Varredura de acesso: cada área protegida, aberta por quem não deveria."""
from django.contrib.auth.models import User
from django.test import TestCase

from contas.models import PerfilAgente
from destinations.models import Destino

PROTEGIDAS = [
    '/agencia/', '/agencia/minha-agencia/', '/agencia/orcamentos/1/pdf/',
    '/minha-conta/', '/minha-conta/meus-dados/', '/minha-conta/excluir/',
    '/painel/', '/painel/destinations/destino/', '/painel/agencia/orcamento/',
    '/painel/destinations/interessado/', '/painel/auth/user/',
]


class VarreduraDeAcessoTests(TestCase):
    def setUp(self):
        Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        usuario = User.objects.create_user('alfa', 'alfa@agencia.com', 'senha-boa-123')
        self.agencia = PerfilAgente.objects.create(
            usuario=usuario, razao_social='Alfa Turismo', cnpj='11222333000181', cadastur='1',
            whatsapp='11999990000', aprovado=True)

    def test_sem_login_nada_protegido_abre(self):
        for url in PROTEGIDAS:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertIn(resposta.status_code, (302, 404))
                if resposta.status_code == 302:
                    # o painel passa pelo /painel/login/, que manda para o Entrar do site
                    if resposta.url.startswith('/painel/login/'):
                        resposta = self.client.get(resposta.url)
                    self.assertIn('/entrar/', resposta.url)
        resposta = self.client.post('/agencia/orcamentos/criar/bonito/', {'cliente_nome': 'X'})
        self.assertEqual(resposta.status_code, 302)

    def test_agencia_nao_entra_no_painel_do_dono(self):
        self.client.force_login(self.agencia.usuario)
        for url in [u for u in PROTEGIDAS if u.startswith('/painel/')]:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertNotEqual(resposta.status_code, 200)

    def test_agencia_nao_aprovada_nao_orca(self):
        self.agencia.aprovado = False
        self.agencia.save()
        self.client.force_login(self.agencia.usuario)
        self.assertEqual(self.client.get('/agencia/').status_code, 302)
        resposta = self.client.post('/agencia/orcamentos/criar/bonito/', {'cliente_nome': 'X'})
        self.assertEqual(resposta.status_code, 302)

    def test_equipe_sem_ser_dono_nao_ve_interessados(self):
        from contas.dois_fatores import CHAVE_OK
        equipe = User.objects.create_user('equipe', 'e@x.com', 'senha-boa-123', is_staff=True)
        self.client.force_login(equipe)
        sessao = self.client.session
        sessao[CHAVE_OK] = equipe.pk
        sessao.save()
        self.assertEqual(self.client.get('/painel/destinations/interessado/').status_code, 403)
        self.assertEqual(self.client.get('/painel/auth/user/').status_code, 403)


class IpAtrasDoProxyTests(TestCase):
    def test_ip_falso_no_cabecalho_nao_dribla_o_limite(self):
        from django.test import RequestFactory, override_settings
        from soar.seguranca import ip_do_cliente
        pedido = RequestFactory().get('/', REMOTE_ADDR='127.0.0.1',
                                      HTTP_X_FORWARDED_FOR='1.2.3.4, 200.10.20.30')
        with override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')):
            self.assertEqual(ip_do_cliente(pedido), '200.10.20.30')
        # sem proxy configurado, o cabeçalho é ignorado
        self.assertEqual(ip_do_cliente(pedido), '127.0.0.1')
