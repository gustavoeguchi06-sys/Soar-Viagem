"""Pedidos do dono de 21/10/2026.

1. Aviso por e-mail para a agência quando a Soar indica um cliente.
2. Orçamentos emitidos aparecem no painel da agência, para acompanhar.
3. CNPJ pode repetir (vários agentes) e o nome do agente aparece.
4. CADASTUR é o próprio CNPJ.
5. CPF no "Saiba mais", e o dono busca por ele.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import PerfilAgente
from destinations.models import Destino, Interessado

from ..models import Orcamento

SENHA = 'senha-boa-123'
CPF = '529.982.247-25'


def _agente(login, nome, cnpj, razao='Alfa Turismo', aprovado=True, email=True):
    usuario = User.objects.create_user(login, (login + '@agencia.com') if email else '', SENHA,
                                       first_name=nome)
    return PerfilAgente.objects.create(usuario=usuario, razao_social=razao, cnpj=cnpj,
                                       whatsapp='11999990000', aprovado=aprovado)


def _entrar_no_painel(client, usuario):
    from contas.dois_fatores import CHAVE_OK
    client.force_login(usuario)
    sessao = client.session
    sessao[CHAVE_OK] = usuario.pk
    sessao.save()


class AvisoDeClienteIndicadoTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.ana = _agente('ana', 'Ana Lima', '11222333000181')
        self.bia = _agente('bia', 'Bia Rocha', '11222333000181')
        self.sem_email = _agente('cris', 'Cris Melo', '11444777000161', razao='Beta', email=False)
        self.pessoa = Interessado.objects.create(
            destino=self.destino, nome='Carlos Souza', cpf=CPF, email='carlos@exemplo.com',
            whatsapp='(11) 98888-7777', cep='01310-100')
        self.dono = User.objects.create_superuser('dono', 'd@x.com', SENHA)
        self.editar = reverse('admin:destinations_interessado_change', args=[self.pessoa.pk])

    def _marcar(self, *agentes):
        _entrar_no_painel(self.client, self.dono)
        return self.client.post(self.editar, {'agencias': [a.pk for a in agentes]}, follow=True)

    def test_agencia_marcada_recebe_email(self):
        resposta = self._marcar(self.ana)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ana@agencia.com'])
        self.assertIn('Bonito', email.subject)
        self.assertIn('Carlos Souza', email.body)
        self.assertIn('/agencia/', email.body)
        # o contato do cliente fica no painel, não no e-mail
        self.assertNotIn('carlos@exemplo.com', email.body)
        self.assertNotIn(CPF, email.body)
        self.assertContains(resposta, 'Aviso por e-mail enviado para: Ana Lima')

    def test_quem_ja_estava_marcado_nao_recebe_de_novo(self):
        self._marcar(self.ana)
        mail.outbox.clear()
        self._marcar(self.ana, self.bia)
        self.assertEqual([m.to for m in mail.outbox], [['bia@agencia.com']])

    def test_agencia_sem_email_gera_aviso_para_o_dono(self):
        resposta = self._marcar(self.sem_email)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(resposta, 'Sem e-mail cadastrado')
        self.assertIn(self.sem_email, self.pessoa.agencias.all())


class CpfDoInteressadoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.url = reverse('destinations:interesse', args=['bonito'])

    def _dados(self, **extra):
        return {'nome': 'Ana Souza', 'cpf': '52998224725', 'email': 'ana@exemplo.com',
                'whatsapp': '11988887777', 'cep': '01310100', **extra}

    def test_cpf_grava_formatado(self):
        self.client.post(self.url, self._dados())
        self.assertEqual(Interessado.objects.get().cpf, CPF)

    def test_cpf_e_obrigatorio_e_validado(self):
        for cpf in ('', '12345678900', '11111111111', '123'):
            self.client.post(self.url, self._dados(cpf=cpf))
        self.assertFalse(Interessado.objects.exists())

    def test_campo_aparece_no_saiba_mais(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'name="cpf"')
        self.assertContains(resposta, 'data-mascara="cpf"')

    def test_dono_busca_pelo_cpf_com_ou_sem_pontos_e_ve_o_historico(self):
        antigo = Interessado.objects.create(destino=self.destino, nome='Ana Souza', cpf=CPF,
                                            email='a@x.com', whatsapp='1', cep='1')
        novo = Interessado.objects.create(destino=self.destino, nome='Ana S.', cpf=CPF,
                                          email='a@x.com', whatsapp='1', cep='1')
        Interessado.objects.create(destino=self.destino, nome='Outra Pessoa', cpf='111.444.777-35',
                                   email='o@x.com', whatsapp='1', cep='1')
        _entrar_no_painel(self.client, User.objects.create_superuser('dono', 'd@x.com', SENHA))
        lista = reverse('admin:destinations_interessado_changelist')
        for termo in ('52998224725', CPF):
            resposta = self.client.get(lista, {'q': termo})
            self.assertContains(resposta, 'Ana Souza')
            self.assertNotContains(resposta, 'Outra Pessoa')
        with self.settings(SISTEMA_RESERVAS_URL='http://www.reservassoar.com.br/login'):
            ficha = self.client.get(reverse('admin:destinations_interessado_change',
                                            args=[novo.pk]))
        self.assertContains(ficha, 'Já viajou com a Soar?')
        self.assertContains(ficha, antigo.criado_em.strftime('%d/%m/%Y'))
        self.assertContains(ficha, 'reservassoar.com.br')

    def test_agencia_nao_ve_o_cpf(self):
        ana = _agente('ana', 'Ana Lima', '11222333000181')
        pessoa = Interessado.objects.create(destino=self.destino, nome='Ana Souza', cpf=CPF,
                                            email='a@x.com', whatsapp='1', cep='1')
        pessoa.agencias.add(ana)
        self.client.force_login(ana.usuario)
        resposta = self.client.get(reverse('agencia:painel'))
        self.assertContains(resposta, 'Ana Souza')
        self.assertNotContains(resposta, CPF)


class VariosAgentesPorCnpjTests(TestCase):
    def _cadastrar(self, login, nome):
        return self.client.post(reverse('contas:cadastro_agente'), {
            'first_name': nome, 'email': login + '@agencia.com', 'username': login,
            'password1': 'Senha-forte-123', 'password2': 'Senha-forte-123',
            'razao_social': 'Alfa Turismo', 'cnpj': '11.222.333/0001-81',
            'whatsapp': '11988887777', 'aceite_privacidade': 'on',
        })

    def test_mesmo_cnpj_cadastra_dois_agentes(self):
        cache.clear()
        self._cadastrar('ana', 'Ana Lima')
        self._cadastrar('bia', 'Bia Rocha')
        agentes = PerfilAgente.objects.filter(cnpj='11222333000181')
        self.assertEqual(agentes.count(), 2)
        self.assertEqual({a.cadastur for a in agentes}, {'11.222.333/0001-81'})

    def test_formulario_nao_pede_cadastur_e_pede_nome_do_agente(self):
        resposta = self.client.get(reverse('contas:cadastro_agente'))
        self.assertNotContains(resposta, 'name="cadastur"')
        self.assertContains(resposta, 'Nome do agente de viagens')

    def test_nome_do_agente_aparece_para_o_dono(self):
        ana = _agente('ana', 'Ana Lima', '11222333000181')
        self.assertTrue(str(ana).startswith('Ana Lima — Alfa Turismo'))
        _entrar_no_painel(self.client, User.objects.create_superuser('dono', 'd@x.com', SENHA))
        self.assertContains(self.client.get(reverse('admin:contas_perfilagente_changelist')),
                            'Ana Lima')
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        pessoa = Interessado.objects.create(destino=destino, nome='X', cpf=CPF, email='x@x.com',
                                            whatsapp='1', cep='1')
        ficha = self.client.get(reverse('admin:destinations_interessado_change', args=[pessoa.pk]))
        self.assertContains(ficha, 'Ana Lima — Alfa Turismo')


class OrcamentosNoPainelDaAgenciaTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.ana = _agente('ana', 'Ana Lima', '11222333000181')
        self.bia = _agente('bia', 'Bia Rocha', '11222333000181')        # mesma agência
        self.outra = _agente('zeca', 'Zeca', '11444777000161', razao='Beta Viagens')

        def orc(agente, cliente, **extra):
            return Orcamento.objects.create(agencia=agente, destino=self.destino,
                                            cliente_nome=cliente, acomodacao='casal',
                                            pessoas=2, valor=6000, **extra)
        self.da_ana = orc(self.ana, 'Cliente da Ana')
        self.da_bia = orc(self.bia, 'Cliente da Bia', status='aceito')
        self.de_fora = orc(self.outra, 'Cliente de Outra Agencia')
        self.vencido = orc(self.ana, 'Cliente Vencido',
                           valido_ate=timezone.now() - timedelta(hours=1))

    def test_lista_mostra_os_da_agencia_toda_e_nao_os_de_outra(self):
        self.client.force_login(self.ana.usuario)
        resposta = self.client.get(reverse('agencia:orcamentos'))
        for nome in ('Cliente da Ana', 'Cliente da Bia', 'Cliente Vencido'):
            self.assertContains(resposta, nome)
        self.assertNotContains(resposta, 'Cliente de Outra Agencia')
        self.assertContains(resposta, 'Bia Rocha')   # vários agentes: mostra quem fez
        self.assertEqual(resposta.context['resumo']['aceitos'], 1)

    def test_visao_geral_mostra_os_ultimos(self):
        self.client.force_login(self.ana.usuario)
        resposta = self.client.get(reverse('agencia:painel'))
        self.assertContains(resposta, 'Últimos orçamentos')
        self.assertContains(resposta, self.da_ana.codigo)

    def test_filtros(self):
        self.client.force_login(self.ana.usuario)
        url = reverse('agencia:orcamentos')
        nomes = lambda f: [o.cliente_nome for o in self.client.get(url, {'situacao': f}).context['orcamentos']]
        self.assertEqual(nomes('vencido'), ['Cliente Vencido'])
        self.assertEqual(nomes('aceito'), ['Cliente da Bia'])
        self.assertEqual(nomes('enviado'), ['Cliente da Ana'])

    def test_so_quem_fez_muda_a_situacao(self):
        self.client.force_login(self.ana.usuario)
        self.client.post(reverse('agencia:orcamento_situacao', args=[self.da_ana.pk]),
                         {'situacao': 'aceito'})
        self.da_ana.refresh_from_db()
        self.assertEqual(self.da_ana.status, 'aceito')
        resposta = self.client.post(reverse('agencia:orcamento_situacao', args=[self.da_bia.pk]),
                                    {'situacao': 'recusado'})
        self.assertEqual(resposta.status_code, 404)
        self.da_bia.refresh_from_db()
        self.assertEqual(self.da_bia.status, 'aceito')

    def test_situacao_so_por_post_e_valor_valido(self):
        self.client.force_login(self.ana.usuario)
        url = reverse('agencia:orcamento_situacao', args=[self.da_ana.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {'situacao': 'qualquer'})
        self.da_ana.refresh_from_db()
        self.assertEqual(self.da_ana.status, 'enviado')

    def test_pdf_de_colega_da_mesma_agencia_abre_e_de_outra_nao(self):
        self.client.force_login(self.ana.usuario)
        self.assertEqual(self.client.get(
            reverse('agencia:orcamento_pdf', args=[self.da_bia.pk])).status_code, 200)
        self.assertEqual(self.client.get(
            reverse('agencia:orcamento_pdf', args=[self.de_fora.pk])).status_code, 404)
