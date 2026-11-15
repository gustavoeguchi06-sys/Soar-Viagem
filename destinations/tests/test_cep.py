"""Endereço do CEP no painel do dono (destinations/cep.py)."""
import io
import json
from unittest import mock
from urllib import error

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import Destino, Interessado

VIACEP = {'cep': '11718-030', 'logradouro': 'Rua das Gaivotas', 'complemento': 'até 300',
          'bairro': 'Boqueirão', 'localidade': 'Praia Grande', 'uf': 'SP'}


def _resposta(dados):
    return mock.MagicMock(__enter__=lambda s: io.BytesIO(json.dumps(dados).encode()),
                          __exit__=lambda *a: False)


@override_settings(CEP_CONSULTA_ATIVA=True)
class EnderecoDoCepTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.url = reverse('destinations:interesse', args=['bonito'])
        self.dados = {'nome': 'Ana Souza', 'cpf': '52998224725', 'email': 'ana@exemplo.com',
                      'whatsapp': '11988887777', 'cep': '11718030'}

    def _dono(self):
        from agencia.tests.test_pedidos_do_dono import _entrar_no_painel
        _entrar_no_painel(self.client, User.objects.create_superuser('dono', 'd@x.com', 'Senha-1234-x'))

    def test_saiba_mais_guarda_o_endereco_do_cep(self):
        with mock.patch('destinations.cep.http.urlopen', return_value=_resposta(VIACEP)) as chamada:
            self.client.post(self.url, self.dados)
        self.assertIn('/11718030/json/', chamada.call_args[0][0].full_url)
        pedido = Interessado.objects.get()
        self.assertEqual((pedido.cep_endereco, pedido.cep_bairro, pedido.cep_cidade, pedido.cep_uf),
                         ('Rua das Gaivotas, até 300', 'Boqueirão', 'Praia Grande', 'SP'))
        self.assertIsNotNone(pedido.cep_consultado_em)

    def test_cliente_nao_ve_o_endereco(self):
        with mock.patch('destinations.cep.http.urlopen', return_value=_resposta(VIACEP)):
            resposta = self.client.post(self.url, self.dados, follow=True)
        self.assertNotContains(resposta, 'Rua das Gaivotas')

    def test_viacep_fora_nao_impede_o_pedido_e_o_painel_tenta_de_novo(self):
        with mock.patch('destinations.cep.http.urlopen', side_effect=error.URLError('fora')):
            self.client.post(self.url, self.dados)
        pedido = Interessado.objects.get()
        self.assertIsNone(pedido.cep_consultado_em)
        self._dono()
        ficha = reverse('admin:destinations_interessado_change', args=[pedido.pk])
        with mock.patch('destinations.cep.http.urlopen', side_effect=error.URLError('fora')):
            self.assertContains(self.client.get(ficha), 'Não deu para consultar o CEP agora')
        with mock.patch('destinations.cep.http.urlopen', return_value=_resposta(VIACEP)):
            resposta = self.client.get(ficha)
        self.assertContains(resposta, 'Rua das Gaivotas, até 300 — Boqueirão')
        self.assertContains(resposta, 'Praia Grande/SP')
        # ficou gravado: a lista mostra a cidade sem consultar de novo
        with mock.patch('destinations.cep.http.urlopen') as chamada:
            lista = self.client.get(reverse('admin:destinations_interessado_changelist'))
        chamada.assert_not_called()
        self.assertContains(lista, 'Praia Grande/SP')

    def test_cep_que_nao_existe(self):
        with mock.patch('destinations.cep.http.urlopen', return_value=_resposta({'erro': True})):
            self.client.post(self.url, self.dados)
        pedido = Interessado.objects.get()
        self.assertIsNotNone(pedido.cep_consultado_em)
        self._dono()
        ficha = reverse('admin:destinations_interessado_change', args=[pedido.pk])
        self.assertContains(self.client.get(ficha), 'CEP não encontrado')

    def test_busca_por_cidade_no_painel(self):
        with mock.patch('destinations.cep.http.urlopen', return_value=_resposta(VIACEP)):
            self.client.post(self.url, self.dados)
        self._dono()
        lista = self.client.get(reverse('admin:destinations_interessado_changelist'),
                                {'q': 'Praia Grande'})
        self.assertContains(lista, 'Ana Souza')
