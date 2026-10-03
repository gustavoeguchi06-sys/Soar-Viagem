"""Painel da agência parceira: cada agência vê só o que é dela."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import PerfilAgente
from destinations.models import Destino, Saida

from .models import Orcamento

SENHA = 'senha-boa-123'


def _agencia(nome, cnpj, aprovado=True):
    usuario = User.objects.create_user(nome, nome + '@agencia.com', SENHA)
    return PerfilAgente.objects.create(usuario=usuario, razao_social=nome.title() + ' Turismo',
                                       cnpj=cnpj, cadastur='123', whatsapp='11999990000',
                                       aprovado=aprovado)


class PainelAgenciaTests(TestCase):
    def setUp(self):
        cache.clear()   # o limite de orçamentos por hora conta no cache
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
        self.criar = reverse('agencia:orcamento_criar', args=['bonito'])
        self.dados = {'cliente_nome': 'Bruno', 'cliente_email': 'bruno@gmail.com',
                      'cliente_telefone': '11977776666',
                      'saida': self.saida.pk, 'acomodacao': 'casal', 'pessoas': 2}

    def entrar(self, agencia):
        self.client.force_login(agencia.usuario)

    def test_painel_so_tem_visao_geral_e_minha_agencia(self):
        self.entrar(self.ag1)
        resposta = self.client.get(reverse('agencia:painel'))
        self.assertContains(resposta, 'Visão geral')
        self.assertContains(resposta, 'Minha agência')
        for aba in ('Reservas dos clientes', '>Orçamentos<', 'Novo orçamento'):
            self.assertNotContains(resposta, aba)
        self.assertEqual(self.client.get('/agencia/orcamentos/').status_code, 404)
        self.assertEqual(self.client.get('/agencia/reservas/').status_code, 404)

    def test_card_da_viagem_tem_o_orcamento(self):
        pagina = self.destino.get_absolute_url()
        resposta = self.client.get(pagina)
        self.assertContains(resposta, 'Saiba mais</summary>')
        self.assertNotContains(resposta, self.criar)
        self.entrar(self.ag1)
        resposta = self.client.get(pagina)
        self.assertContains(resposta, 'action="{}"'.format(self.criar))
        self.assertContains(resposta, 'name="cliente_nome"')
        self.assertContains(resposta, 'name="idades_criancas"')
        self.assertNotContains(resposta, 'Reservar agora')
        # vindo do calendário, a data já vem marcada
        resposta = self.client.get(pagina, {'saida': self.saida.pk})
        self.assertEqual(resposta.context['saida_marcada'], str(self.saida.pk))

    def test_quarto_esgotado_na_data_nao_vira_orcamento(self):
        self.saida.quartos_casal = 0
        self.saida.quartos_triplo = 2
        self.saida.save()
        self.entrar(self.ag1)
        # a data leva os quartos de cada tipo para a lista de acomodações
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'data-quartos="casal:0,triplo:2"')
        resposta = self.client.post(self.criar, self.dados)
        self.assertContains(resposta, 'Esse quarto está esgotado nesta data.')
        self.assertFalse(Orcamento.objects.exists())
        self.client.post(self.criar, {**self.dados, 'acomodacao': 'triplo'})
        self.assertTrue(Orcamento.objects.exists())

    def test_cria_orcamento_na_viagem_com_72_horas_e_aviso(self):
        self.entrar(self.ag1)
        antes = timezone.now()
        resposta = self.client.post(self.criar, self.dados)
        orcamento = Orcamento.objects.get()
        self.assertRedirects(resposta, '{}?orcamento={}#reservar'.format(
            self.destino.get_absolute_url(), orcamento.pk), fetch_redirect_response=False)
        self.assertEqual(orcamento.agencia, self.ag1)
        self.assertEqual(orcamento.destino, self.destino)
        self.assertEqual(orcamento.saida_texto, self.saida.texto)
        self.assertEqual(orcamento.cliente_telefone, '(11) 97777-6666')
        # casal: 3.000 por adulto x 2 adultos
        self.assertEqual(orcamento.valor, Decimal('6000'))
        validade = orcamento.valido_ate - antes
        self.assertTrue(timedelta(hours=71, minutes=59) < validade <= timedelta(hours=72, minutes=1))

        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, 'Orçamento {} criado'.format(orcamento.codigo))
        # o aviso abre sozinho como pop-up
        self.assertContains(pagina, 'class="popup popup--aviso" data-popup data-abrir-ja')
        self.assertContains(pagina, 'IMPORTANTE:')
        self.assertContains(pagina, 'Este orçamento não garante a reserva ou a disponibilidade '
                                    'dos serviços apresentados.')
        self.assertContains(pagina, 'A cotação é válida por 72 horas, estando sujeita à '
                                    'disponibilidade e à alteração de valores após esse período.')

        # outra agência não vê o orçamento de ninguém pela página
        self.entrar(self.ag2)
        self.assertNotContains(self.client.get(resposta.url), 'IMPORTANTE:')

    def test_manda_o_pdf_para_o_email_do_responsavel(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'idades_criancas': '5'})
        orcamento = Orcamento.objects.get()
        self.assertIsNotNone(orcamento.enviado_em)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bruno@gmail.com'])
        self.assertEqual(email.reply_to, ['alfa@agencia.com'])
        self.assertIn(orcamento.codigo, email.subject)
        self.assertIn('Olá, Bruno!', email.body)
        self.assertIn('IMPORTANTE:', email.body)
        nome, conteudo, tipo = email.attachments[0]
        self.assertEqual((nome, tipo), ('orcamento-{}.pdf'.format(orcamento.codigo),
                                        'application/pdf'))
        self.assertTrue(conteudo.startswith(b'%PDF'))
        self.assertContains(self.client.get(resposta.url), 'PDF enviado para <b>bruno@gmail.com</b>')

    def test_sem_email_o_popup_volta_aberto_com_erro(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'cliente_email': ''})
        self.assertContains(resposta, 'Informe o e-mail para onde vai o orçamento.')
        self.assertTrue(resposta.context['form_orcamento'].erro_no_popup)
        resposta = self.client.post(self.criar, {**self.dados, 'cliente_email': 'bruno@'})
        self.assertContains(resposta, 'Esse e-mail não parece certo.')
        self.assertFalse(Orcamento.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_email_que_falha_nao_perde_o_orcamento(self):
        self.entrar(self.ag1)
        with mock.patch('agencia.views.EmailMessage.send', side_effect=OSError('smtp fora')):
            resposta = self.client.post(self.criar, self.dados)
        orcamento = Orcamento.objects.get()
        self.assertIsNone(orcamento.enviado_em)
        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, 'Não conseguimos enviar o e-mail')
        self.assertContains(pagina, reverse('agencia:orcamento_pdf', args=[orcamento.pk]))

    def test_pdf_tem_todas_as_informacoes_do_pacote(self):
        from destinations.conteudo import montar_viagem
        from .pdf import _estilos, _pacote

        def textos(flowables):
            for f in flowables:
                if hasattr(f, '_content'):          # KeepTogether
                    yield from textos(f._content)
                elif hasattr(f, 'getPlainText'):
                    yield f.getPlainText()

        viagem = montar_viagem(self.destino, [])
        texto = '\n'.join(textos(_pacote(self.destino, viagem, _estilos())))
        for secao in ('Sobre a viagem', 'Destaques da viagem', 'Roteiro dia a dia',
                      'O pacote inclui', 'Hospedagem', 'Informações importantes',
                      'Perguntas frequentes'):
            self.assertIn(secao, texto)
        dia = viagem['roteiro'][0]
        self.assertIn(dia['resumo'], texto)
        for topico in dia['topicos']:                 # o roteiro vai completo
            self.assertIn(topico.replace('→', '-'), texto)
        self.assertIn(viagem['faq'][0]['pergunta'], texto)

    def test_pdf_so_para_a_agencia_dona(self):
        self.entrar(self.ag1)
        self.client.post(self.criar, self.dados)
        pdf = reverse('agencia:orcamento_pdf', args=[Orcamento.objects.get().pk])
        resposta = self.client.get(pdf)
        self.assertEqual(resposta['Content-Type'], 'application/pdf')
        self.assertTrue(resposta.content.startswith(b'%PDF'))
        self.entrar(self.ag2)
        self.assertEqual(self.client.get(pdf).status_code, 404)

    def test_limite_de_orcamentos_por_hora(self):
        from soar.seguranca import LIMITE_ORCAMENTO
        self.entrar(self.ag1)
        with mock.patch.object(LIMITE_ORCAMENTO, 'tentativas', 1):
            self.client.post(self.criar, self.dados)
            resposta = self.client.post(self.criar, self.dados)
        self.assertContains(resposta, 'Muitos orçamentos enviados na última hora.')
        self.assertEqual(Orcamento.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_vence_depois_de_72_horas(self):
        self.entrar(self.ag1)
        self.client.post(self.criar, self.dados)
        orcamento = Orcamento.objects.get()
        self.assertFalse(orcamento.vencido)
        orcamento.valido_ate = timezone.now() - timedelta(minutes=1)
        self.assertTrue(orcamento.vencido)

    def test_orcamento_recusa_data_de_outro_destino(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'saida': self.saida_outro.pk})
        self.assertContains(resposta, 'Escolha uma das datas da viagem.')
        self.assertFalse(Orcamento.objects.exists())

    def test_sem_nome_do_cliente_volta_com_erro(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'cliente_nome': ''})
        self.assertContains(resposta, 'Informe o nome do responsável.')
        # o que a agência marcou continua marcado
        self.assertEqual(resposta.context['acomodacao_marcada'], 'casal')
        self.assertFalse(Orcamento.objects.exists())

    def test_criancas_vao_como_adicional_dos_adultos(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'acomodacao': 'crianca'})
        self.assertEqual(resposta.status_code, 200)
        resposta = self.client.post(self.criar, {**self.dados, 'idades_criancas': '4, 9'})
        self.assertContains(resposta, 'de 0 a 8 anos')
        self.assertFalse(Orcamento.objects.exists())

        resposta = self.client.post(self.criar, {**self.dados, 'idades_criancas': '4 e 7'})
        orcamento = Orcamento.objects.get()
        self.assertEqual(orcamento.idades_criancas, '4, 7')
        self.assertEqual(orcamento.valor, Decimal('6000'))   # criança fica fora da conta
        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, '2 (4 e 7 anos)')
        self.assertContains(pagina, 'crianças sob consulta')

    def test_viagem_sem_preco_fica_sob_consulta(self):
        self.entrar(self.ag1)
        self.client.post(reverse('agencia:orcamento_criar', args=['jalapao']),
                         {'cliente_nome': 'Bruno', 'cliente_email': 'bruno@gmail.com',
                          'acomodacao': 'casal', 'pessoas': 2})
        self.assertIsNone(Orcamento.objects.get().valor)

    def test_cliente_e_agencia_nao_aprovada_nao_orcam(self):
        self.client.force_login(self.cliente)
        self.assertRedirects(self.client.get(reverse('agencia:painel')),
                             reverse('contas:minha_conta'), fetch_redirect_response=False)
        self.client.post(self.criar, self.dados)
        pendente = _agencia('gama', '11222333000262', aprovado=False)
        self.entrar(pendente)
        self.assertRedirects(self.client.post(self.criar, self.dados),
                             reverse('contas:agente_area'), fetch_redirect_response=False)
        self.client.logout()
        resposta = self.client.post(self.criar, self.dados)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('contas:entrar'), resposta.url)
        self.assertFalse(Orcamento.objects.exists())

    def test_agencia_aprovada_cai_no_painel_ao_entrar(self):
        resposta = self.client.post(reverse('contas:entrar'),
                                    {'username': 'alfa', 'password': SENHA})
        self.assertRedirects(resposta, reverse('agencia:painel'), fetch_redirect_response=False)


class InteressadosTests(TestCase):
    """Pessoa física que pediu "Saiba mais": só o dono vê e escolhe a agência."""

    def setUp(self):
        from destinations.models import Interessado
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.ag1 = _agencia('alfa', '11222333000181')
        self.ag2 = _agencia('beta', '11444777000161')
        self.pessoa = Interessado.objects.create(destino=self.destino, nome='Ana Souza',
                                                 email='ana@exemplo.com',
                                                 whatsapp='(11) 98888-7777', cep='01310-100')

    def test_agencia_ve_so_quem_foi_mandado_para_ela(self):
        self.pessoa.agencias.add(self.ag1)
        self.client.force_login(self.ag1.usuario)
        self.assertContains(self.client.get(reverse('agencia:painel')), 'Ana Souza')
        pagina = self.destino.get_absolute_url()
        form = self.client.get(pagina, {'interessado': self.pessoa.pk}).context['form_orcamento']
        self.assertEqual(form.initial['cliente_nome'], 'Ana Souza')

        self.client.force_login(self.ag2.usuario)
        self.assertNotContains(self.client.get(reverse('agencia:painel')), 'Ana Souza')
        form = self.client.get(pagina, {'interessado': self.pessoa.pk}).context['form_orcamento']
        self.assertNotIn('cliente_nome', form.initial)

    def _entrar_no_painel(self, usuario):
        """Entra já com o código do celular conferido (contas/dois_fatores.py)."""
        from contas.dois_fatores import CHAVE_OK
        self.client.force_login(usuario)
        sessao = self.client.session
        sessao[CHAVE_OK] = usuario.pk
        sessao.save()

    def test_so_o_dono_ve_no_painel(self):
        lista = reverse('admin:destinations_interessado_changelist')
        self._entrar_no_painel(User.objects.create_user('equipe', 'e@x.com', SENHA,
                                                        is_staff=True))
        self.assertEqual(self.client.get(lista).status_code, 403)

        self._entrar_no_painel(User.objects.create_superuser('dono', 'd@x.com', SENHA))
        self.assertContains(self.client.get(lista), 'Ana Souza')
        editar = reverse('admin:destinations_interessado_change', args=[self.pessoa.pk])
        self.assertContains(self.client.get(editar), 'Enviar para as agências')
