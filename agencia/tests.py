"""Painel da agência parceira: cada agência vê só o que é dela."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import PerfilAgente
from destinations.models import Destino, Saida
from reservas.models import Reserva

from .models import Orcamento

SENHA = 'senha-boa-123'


def _agencia(nome, cnpj, aprovado=True):
    usuario = User.objects.create_user(nome, nome + '@agencia.com', SENHA)
    return PerfilAgente.objects.create(usuario=usuario, razao_social=nome.title() + ' Turismo',
                                       cnpj=cnpj, cadastur='123', whatsapp='11999990000',
                                       aprovado=aprovado)


class PainelAgenciaTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                              preco_base=3000)
        self.outro = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        hoje = timezone.localdate()
        self.saida = Saida.objects.create(destino=self.destino, vagas=10,
                                          data_ida=hoje + timedelta(days=40),
                                          data_volta=hoje + timedelta(days=44))
        self.saida_outro = Saida.objects.create(destino=self.outro, vagas=10,
                                                data_ida=hoje + timedelta(days=50),
                                                data_volta=hoje + timedelta(days=55))
        self.ag1 = _agencia('alfa', '11222333000181')
        self.ag2 = _agencia('beta', '11444777000161')
        self.cliente = User.objects.create_user('cliente', 'cliente@exemplo.com', SENHA,
                                                first_name='Ana')
        self.da_ag1 = Reserva.objects.create(usuario=self.cliente, destino=self.destino,
                                             telefone='11988887777', agencia=self.ag1)
        self.da_ag2 = Reserva.objects.create(usuario=self.cliente, destino=self.destino,
                                             agencia=self.ag2)
        self.sem_agencia = Reserva.objects.create(usuario=self.cliente, destino=self.destino)

    def entrar(self, agencia):
        self.client.force_login(agencia.usuario)

    def test_agencia_ve_so_as_reservas_dela(self):
        self.entrar(self.ag1)
        resposta = self.client.get(reverse('agencia:reservas'))
        self.assertEqual(list(resposta.context['reservas']), [self.da_ag1])
        self.assertContains(resposta, 'https://wa.me/5511988887777')

    def test_reserva_de_outra_agencia_da_404(self):
        self.entrar(self.ag1)
        for reserva in (self.da_ag2, self.sem_agencia):
            resposta = self.client.get(reverse('agencia:reserva', args=[reserva.pk]))
            self.assertEqual(resposta.status_code, 404)
            resposta = self.client.post(reverse('agencia:reserva', args=[reserva.pk]),
                                        {'status': 'confirmada'})
            self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Reserva.objects.get(pk=self.da_ag2.pk).status, 'pendente')

    def test_agencia_confirma_e_anota(self):
        self.entrar(self.ag1)
        self.client.post(reverse('agencia:reserva', args=[self.da_ag1.pk]),
                         {'status': 'confirmada', 'nota_agencia': 'Pix até sexta.'})
        self.da_ag1.refresh_from_db()
        self.assertEqual(self.da_ag1.status, 'confirmada')
        self.assertEqual(self.da_ag1.nota_agencia, 'Pix até sexta.')

    def test_cliente_e_agencia_nao_aprovada_nao_entram(self):
        self.client.force_login(self.cliente)
        self.assertRedirects(self.client.get(reverse('agencia:painel')),
                             reverse('contas:minha_conta'), fetch_redirect_response=False)
        pendente = _agencia('gama', '11222333000262', aprovado=False)
        self.entrar(pendente)
        self.assertRedirects(self.client.get(reverse('agencia:reservas')),
                             reverse('contas:agente_area'), fetch_redirect_response=False)
        self.client.logout()
        resposta = self.client.get(reverse('agencia:painel'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('contas:entrar'), resposta.url)

    def test_agencia_aprovada_cai_no_painel_ao_entrar(self):
        resposta = self.client.post(reverse('contas:entrar'),
                                    {'username': 'alfa', 'password': SENHA})
        self.assertRedirects(resposta, reverse('agencia:painel'), fetch_redirect_response=False)

    def test_cria_orcamento_e_outra_agencia_nao_ve(self):
        self.entrar(self.ag1)
        resposta = self.client.post(reverse('agencia:orcamento_novo'), {
            'cliente_nome': 'Bruno', 'cliente_telefone': '11977776666',
            'destino': self.destino.pk, 'saida_escolhida': self.saida.pk,
            'acomodacao': 'casal', 'pessoas': 2, 'valor': '6.500,00', 'status': 'enviado',
        })
        self.assertRedirects(resposta, reverse('agencia:orcamentos'),
                             fetch_redirect_response=False)
        orcamento = Orcamento.objects.get()
        self.assertEqual(orcamento.agencia, self.ag1)
        self.assertEqual(orcamento.valor, Decimal('6500.00'))
        self.assertEqual(orcamento.saida_texto, self.saida.texto)

        self.entrar(self.ag2)
        self.assertEqual(list(self.client.get(reverse('agencia:orcamentos'))
                              .context['orcamentos']), [])
        resposta = self.client.get(reverse('agencia:orcamento_editar', args=[orcamento.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_orcamento_recusa_data_de_outro_destino(self):
        self.entrar(self.ag1)
        resposta = self.client.post(reverse('agencia:orcamento_novo'), {
            'cliente_nome': 'Bruno', 'destino': self.destino.pk,
            'saida_escolhida': self.saida_outro.pk, 'acomodacao': 'casal',
            'pessoas': 2, 'status': 'enviado',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Orcamento.objects.exists())

    def test_link_de_indicacao_marca_a_reserva(self):
        self.client.get(reverse('destinations:home') + '?ag=' + self.ag2.codigo.lower())
        self.client.force_login(User.objects.create_user('novo', 'novo@exemplo.com', SENHA))
        resposta = self.client.get(reverse('reservas:nova', args=['bonito']))
        self.assertContains(resposta, self.ag2.razao_social)
        self.client.post(reverse('reservas:nova', args=['bonito']), {
            'saida_escolhida': self.saida.pk, 'acomodacao': 'casal', 'pessoas': 2,
        })
        self.assertEqual(Reserva.objects.get(usuario__username='novo').agencia, self.ag2)

    def test_codigo_de_agencia_nao_aprovada_e_ignorado(self):
        pendente = _agencia('gama', '11222333000262', aprovado=False)
        self.client.get(reverse('destinations:home') + '?ag=' + pendente.codigo)
        novo = User.objects.create_user('novo', 'novo@exemplo.com', SENHA)
        self.client.force_login(novo)
        self.client.post(reverse('reservas:nova', args=['bonito']), {
            'saida_escolhida': self.saida.pk, 'acomodacao': 'casal', 'pessoas': 2,
        })
        self.assertIsNone(Reserva.objects.get(usuario=novo).agencia)
