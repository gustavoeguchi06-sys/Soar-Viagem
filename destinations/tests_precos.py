"""Preço por pessoa em cada tipo de quarto, quartos por data e faixa de serviços."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .conteudo import tabela_de_precos
from .models import Destino, PrecoQuarto, Saida, ServicoViagem


class PrecosPorQuartoTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')

    def test_cada_quarto_tem_o_seu_preco(self):
        PrecoQuarto.objects.create(destino=self.destino, tipo='single', preco=Decimal('5100'))
        PrecoQuarto.objects.create(destino=self.destino, tipo='casal', preco=Decimal('3900'))
        PrecoQuarto.objects.create(destino=self.destino, tipo='triplo', preco=Decimal('2950.50'))
        self.assertEqual(tabela_de_precos(self.destino),
                         {'single': Decimal('5100'), 'casal': Decimal('3900'),
                          'triplo': Decimal('2950.50')})
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'R$ 5.100')
        self.assertContains(resposta, 'R$ 2.950,50')
        # só os tipos cadastrados aparecem
        self.assertNotContains(resposta, 'value="duplo"')
        # não existe quarto quádruplo
        self.assertNotContains(resposta, 'Quádruplo')

    def test_a_partir_de_e_o_menor_preco_e_se_atualiza_sozinho(self):
        casal = PrecoQuarto.objects.create(destino=self.destino, tipo='casal', preco=Decimal('3900'))
        PrecoQuarto.objects.create(destino=self.destino, tipo='triplo', preco=Decimal('3500'))
        self.destino.refresh_from_db()
        self.assertEqual(self.destino.preco_base, Decimal('3500'))
        casal.preco = Decimal('3000')
        casal.save()
        self.destino.refresh_from_db()
        self.assertEqual(self.destino.preco_base, Decimal('3000'))
        PrecoQuarto.objects.filter(destino=self.destino).delete()
        self.destino.refresh_from_db()
        self.assertIsNone(self.destino.preco_base)

    def test_orcamento_usa_o_preco_do_quarto_escolhido(self):
        from contas.models import PerfilAgente
        from agencia.models import Orcamento
        PrecoQuarto.objects.create(destino=self.destino, tipo='triplo', preco=Decimal('3100'))
        usuario = User.objects.create_user('alfa', 'alfa@agencia.com', 'senha-boa-123')
        PerfilAgente.objects.create(usuario=usuario, razao_social='Alfa Turismo',
                                    cnpj='11222333000181', cadastur='1', whatsapp='11999990000',
                                    aprovado=True)
        self.client.force_login(usuario)
        self.client.post(reverse('agencia:orcamento_criar', args=['bonito']), {
            'cliente_nome': 'Bruno', 'cliente_email': 'bruno@gmail.com',
            'acomodacao': 'triplo', 'pessoas': 3})
        self.assertEqual(Orcamento.objects.get().valor, Decimal('9300'))


class QuartosPorDataTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        hoje = timezone.localdate()
        self.saida = Saida.objects.create(destino=self.destino, data_ida=hoje + timedelta(days=30),
                                          data_volta=hoje + timedelta(days=34),
                                          quartos_casal=4, quartos_single=0)

    def test_data_mostra_os_quartos_de_cada_tipo(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Casal: 4 quartos')
        self.assertContains(resposta, 'Single: esgotado')
        self.assertNotContains(resposta, 'Triplo:')

    def test_data_esgota_quando_todos_os_quartos_acabam(self):
        self.assertFalse(self.saida.esgotada)
        self.saida.quartos_casal = 0
        self.assertTrue(self.saida.esgotada)


class FaixaDeServicosTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Noronha', slug='noronha', descricao='Mar.')

    def test_sem_cadastro_usa_a_faixa_padrao(self):
        self.assertContains(self.client.get(self.destino.get_absolute_url()), 'Transporte<br>confortável')

    def test_faixa_cadastrada_no_painel(self):
        ServicoViagem.objects.create(destino=self.destino, icone='ic-barco', titulo='Passeio',
                                     sub='de barco', ordem=1)
        ServicoViagem.objects.create(destino=self.destino, icone='ic-aviao', titulo='Aéreo',
                                     sub='incluso', ordem=0)
        resposta = self.client.get(self.destino.get_absolute_url()).content.decode()
        self.assertIn('href="#ic-barco"', resposta)
        self.assertNotIn('Transporte<br>confortável', resposta)
        self.assertLess(resposta.index('Aéreo<br>incluso'), resposta.index('Passeio<br>de barco'))

    def test_painel_mostra_o_seletor_de_icones(self):
        from contas.dois_fatores import CHAVE_OK
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        sessao = self.client.session
        sessao[CHAVE_OK] = dono.pk
        sessao.save()
        resposta = self.client.get(reverse('admin:destinations_destino_change',
                                           args=[self.destino.pk]))
        self.assertContains(resposta, 'Preços por quarto')
        self.assertContains(resposta, 'Faixa de serviços da página')
        self.assertContains(resposta, 'symbol id="ic-aviao"')


class SoFotosDoDonoTests(TestCase):
    """A página mostra só as fotos cadastradas, sem completar com ilustrações."""

    def test_sem_foto_nao_tem_galeria_nem_miniaturas(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        resposta = self.client.get(destino.get_absolute_url())
        self.assertNotContains(resposta, 'id="galeria"')
        self.assertNotContains(resposta, 'class="hero__thumbs"')
        self.assertNotContains(resposta, 'data-hero="1"')
        # o topo ainda tem uma imagem, só uma
        self.assertEqual(len(resposta.context['viagem']['fotos']), 1)
        self.assertEqual(resposta.context['viagem']['galeria'], [])
        # a hospedagem também não completa com desenhos de quarto
        self.assertNotContains(resposta, 'class="hosp-mini"')
