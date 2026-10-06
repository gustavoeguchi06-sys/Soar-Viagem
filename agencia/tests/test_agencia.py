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

from ..models import Orcamento

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
                      'saida': self.saida.pk, 'quartos_casal': 1, 'pessoas_casal': 2}

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

    def test_painel_e_b2b_levam_ao_sistema_de_reservas(self):
        endereco = 'http://www.reservassoar.com.br/login'
        with self.settings(SISTEMA_RESERVAS_URL=endereco):
            self.assertContains(self.client.get(reverse('contas:b2b')), endereco)
            self.entrar(self.ag1)
            resposta = self.client.get(reverse('agencia:painel'))
            self.assertContains(resposta, 'href="{}"'.format(endereco))
            self.assertContains(resposta, 'rel="noopener noreferrer"')
        with self.settings(SISTEMA_RESERVAS_URL=''):
            self.assertNotContains(self.client.get(reverse('agencia:painel')), 'Sistema de reservas')

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
        self.client.post(self.criar, {**self.dados, 'quartos_casal': 0, 'pessoas_casal': 0,
                                      'quartos_triplo': 1, 'pessoas_triplo': 3})
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
        from ..pdf import _estilos, _pacote

        def textos(flowables):
            for f in flowables:
                if hasattr(f, '_content'):          # KeepTogether
                    yield from textos(f._content)
                elif hasattr(f, 'getPlainText'):
                    yield f.getPlainText()

        viagem = montar_viagem(self.destino, [])
        texto = '\n'.join(textos(_pacote(self.destino, viagem, _estilos())))
        for secao in ('Sobre a viagem', 'Destaques da viagem', 'Roteiro dia a dia',
                      'O pacote inclui', 'Hospedagem', 'Informações importantes'):
            self.assertIn(secao, texto)
        dia = viagem['roteiro'][0]
        self.assertIn(dia['resumo'], texto)
        for topico in dia['topicos']:                 # o roteiro vai completo
            self.assertIn(topico.replace('→', '-'), texto)
        # as perguntas frequentes ficam só no site
        self.assertNotIn('Perguntas frequentes', texto)
        self.assertNotIn(viagem['faq'][0]['pergunta'], texto)

    def test_pdf_formas_de_pagamento_entre_o_total_e_a_validade(self):
        from decimal import Decimal
        from .. import pdf

        capturado = {}
        construir = pdf.SimpleDocTemplate.build

        def guardar(doc, corpo, **kwargs):
            capturado['corpo'] = list(corpo)   # o build esvazia a lista
            return construir(doc, corpo, **kwargs)

        self.entrar(self.ag1)
        self.client.post(self.criar, self.dados)
        orcamento = Orcamento.objects.get()
        with mock.patch.object(pdf.SimpleDocTemplate, 'build', guardar):
            pdf.gerar_pdf(orcamento)

        def texto(celula):
            # depois do build, cada célula vira uma tupla com o Paragraph dentro
            celula = celula[0] if isinstance(celula, (list, tuple)) and celula else celula
            return celula.getPlainText() if hasattr(celula, 'getPlainText') else ''

        ficha = next(f for f in capturado['corpo'] if isinstance(f, pdf.Table)
                     and any(texto(linha[0]) == 'Valor total' for linha in f._cellvalues))
        rotulos = [texto(linha[0]) for linha in ficha._cellvalues]
        i = rotulos.index('Formas de pagamento')
        self.assertEqual(rotulos[i - 1], 'Valor total')
        self.assertEqual(rotulos[i + 1], 'Válido até')
        pagamento = texto(ficha._cellvalues[i][1])
        a_vista = pdf._reais(orcamento.valor * (1 - Decimal('0.05')))
        self.assertIn('À vista com 5% de desconto ({})'.format(a_vista), pagamento)
        self.assertIn('Cartão: 1 + 9x sem juros', pagamento)
        self.assertIn('15 dias antes do embarque', pagamento)

    def test_pdf_com_fotos_do_destino_e_do_hotel(self):
        import shutil
        import tempfile
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from PIL import Image as Foto

        from destinations.models import Hospedagem, ImagemDestino

        def jpg(nome):
            saida = BytesIO()
            Foto.new('RGB', (1600, 1000), (30, 120, 80)).save(saida, 'JPEG')
            return SimpleUploadedFile(nome, saida.getvalue(), content_type='image/jpeg')

        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        with override_settings(MEDIA_ROOT=pasta):
            self.destino.imagem_capa = jpg('capa.jpg')
            self.destino.save()
            ImagemDestino.objects.create(destino=self.destino, imagem=jpg('rio.jpg'),
                                         legenda='Rio da Prata')
            Hospedagem.objects.create(destino=self.destino, nome='Pousada Bonito',
                                      imagem=jpg('pousada.jpg'))
            self.entrar(self.ag1)
            self.client.post(self.criar, self.dados)
            from ..pdf import gerar_pdf
            conteudo = gerar_pdf(Orcamento.objects.get())
        sem_fotos = gerar_pdf(Orcamento.objects.create(
            agencia=self.ag1, destino=self.outro, cliente_nome='Ana', pessoas=2))
        # capa, a foto da galeria e a do hotel (o resto é o logo, nos dois)
        self.assertEqual(conteudo.count(b'/Subtype /Image')
                         - sem_fotos.count(b'/Subtype /Image'), 3)
        self.assertLess(len(conteudo), 600 * 1024)   # leve para o e-mail

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
        self.assertEqual(resposta.context['form_orcamento']['quartos_casal'].value(), '1')
        self.assertFalse(Orcamento.objects.exists())

    def test_criancas_vao_como_adicional_dos_adultos(self):
        self.entrar(self.ag1)
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
                          'quartos_casal': 1, 'pessoas_casal': 2})
        self.assertIsNone(Orcamento.objects.get().valor)

    def test_varios_quartos_e_pessoas_ate_a_lotacao(self):
        self.entrar(self.ag1)
        # Bonito: 3.000 por pessoa no casal e no duplo, 2.800 no triplo, 4.400 no single
        resposta = self.client.post(self.criar, {
            **self.dados, 'quartos_casal': 0, 'pessoas_casal': 0,
            'quartos_duplo': 2, 'pessoas_duplo': 3,      # dois duplos, um com 1 pessoa
            'quartos_triplo': 1, 'pessoas_triplo': 2,    # triplo com 2: pode, é menos
            'quartos_single': 1})
        orcamento = Orcamento.objects.get()
        self.assertEqual(orcamento.pessoas, 6)
        self.assertEqual(orcamento.valor, Decimal(3 * 3000 + 2 * 2800 + 1 * 4400))
        self.assertEqual(orcamento.acomodacao_texto,
                         '1 quarto Single, 1 pessoa; 2 quartos Duplo (Twin), 3 pessoas; '
                         '1 quarto Triplo, 2 pessoas')
        pagina = self.client.get(resposta.url)
        self.assertContains(pagina, '2 quartos Duplo (Twin), 3 pessoas')
        self.assertTrue(self.client.get(
            reverse('agencia:orcamento_pdf', args=[orcamento.pk])).content.startswith(b'%PDF'))

    def test_nao_passa_da_lotacao_nem_fica_quarto_vazio(self):
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'pessoas_casal': 3})
        self.assertContains(resposta, 'no máximo 2.')
        resposta = self.client.post(self.criar, {**self.dados, 'quartos_triplo': 2,
                                                 'pessoas_triplo': 7})
        self.assertContains(resposta, 'no máximo 6.')
        resposta = self.client.post(self.criar, {**self.dados, 'quartos_duplo': 2,
                                                 'pessoas_duplo': 1})
        self.assertContains(resposta, 'no mínimo 2 pessoas')
        resposta = self.client.post(self.criar, {**self.dados, 'quartos_casal': 0,
                                                 'pessoas_casal': 0})
        self.assertContains(resposta, 'Escolha pelo menos um quarto.')
        self.assertFalse(Orcamento.objects.exists())

    def test_nao_escolhe_mais_quartos_do_que_a_data_tem(self):
        self.saida.quartos_duplo = 1
        self.saida.save()
        self.entrar(self.ag1)
        resposta = self.client.post(self.criar, {**self.dados, 'quartos_duplo': 2,
                                                 'pessoas_duplo': 4})
        self.assertContains(resposta, 'Nesta data há só 1 quarto Duplo (Twin).')
        self.assertFalse(Orcamento.objects.exists())

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

        # os quartos que a pessoa pediu já vêm no orçamento
        self.pessoa.quartos = [{'tipo': 'triplo', 'quartos': 1, 'pessoas': 2, 'preco': None}]
        self.pessoa.save()
        resposta = self.client.get(reverse('agencia:painel'))
        self.assertContains(resposta, '1 quarto Triplo, 2 pessoas')
        form = self.client.get(pagina, {'interessado': self.pessoa.pk}).context['form_orcamento']
        self.assertEqual((form['quartos_triplo'].value(), form['pessoas_triplo'].value(),
                          form['quartos_casal'].value()), (1, 2, 0))

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

    def test_aba_interessados_so_para_o_dono_com_contador(self):
        inicio = reverse('admin:index')
        lista = reverse('admin:destinations_interessado_changelist')
        self._entrar_no_painel(User.objects.create_user('equipe', 'e@x.com', SENHA,
                                                        is_staff=True))
        self.assertNotContains(self.client.get(inicio), lista)

        self._entrar_no_painel(User.objects.create_superuser('dono', 'd@x.com', SENHA))
        abas = {a['nome']: a for a in self.client.get(inicio).context['abas_painel']}
        self.assertEqual(abas['Interessados']['url'], lista)
        self.assertEqual(abas['Interessados']['contador'], 1)   # ainda não mandado
        self.pessoa.agencias.add(self.ag1)
        abas = {a['nome']: a for a in self.client.get(inicio).context['abas_painel']}
        self.assertEqual(abas['Interessados']['contador'], 0)


class OrcamentosNoPainelTests(TestCase):
    """No painel não se cria nem se altera orçamento: o dono só vê e marca a situação."""

    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.orcamento = Orcamento.objects.create(
            agencia=_agencia('alfa', '11222333000181'), destino=self.destino,
            cliente_nome='Ana Souza', cliente_email='ana@exemplo.com', acomodacao='casal',
            pessoas=2, valor=6000)

    _entrar_no_painel = InteressadosTests._entrar_no_painel

    def test_dono_nao_cria_orcamento(self):
        self._entrar_no_painel(User.objects.create_superuser('dono', 'd@x.com', SENHA))
        lista = self.client.get(reverse('admin:agencia_orcamento_changelist'))
        self.assertContains(lista, 'Ana Souza')
        self.assertNotContains(lista, reverse('admin:agencia_orcamento_add'))
        self.assertEqual(self.client.get(reverse('admin:agencia_orcamento_add')).status_code, 403)

    def test_dono_so_muda_a_situacao(self):
        self._entrar_no_painel(User.objects.create_superuser('dono', 'd@x.com', SENHA))
        editar = reverse('admin:agencia_orcamento_change', args=[self.orcamento.pk])
        self.client.post(editar, {'status': 'aceito', 'cliente_nome': 'Outro Nome',
                                  'valor': '1', 'pessoas': '9'})
        self.orcamento.refresh_from_db()
        self.assertEqual(self.orcamento.status, 'aceito')
        self.assertEqual((self.orcamento.cliente_nome, self.orcamento.valor,
                          self.orcamento.pessoas), ('Ana Souza', 6000, 2))

    def test_equipe_nao_ve_orcamentos(self):
        self._entrar_no_painel(User.objects.create_user('equipe', 'e@x.com', SENHA,
                                                        is_staff=True))
        self.assertEqual(
            self.client.get(reverse('admin:agencia_orcamento_changelist')).status_code, 403)


class InicioDoPainelTests(TestCase):
    """A tela inicial do painel mostra o trabalho de verdade: interessados e orçamentos."""

    _entrar_no_painel = InteressadosTests._entrar_no_painel

    def setUp(self):
        from destinations.models import Interessado
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        Interessado.objects.create(destino=destino, nome='Ana Souza', email='ana@exemplo.com',
                                   whatsapp='(11) 98888-7777', cep='01310-100')
        Orcamento.objects.create(agencia=_agencia('alfa', '11222333000181'), destino=destino,
                                 cliente_nome='Bruno', valor=6000)

    def test_dono_ve_interessados_e_orcamentos(self):
        self._entrar_no_painel(User.objects.create_superuser('dono', 'd@x.com', SENHA))
        resposta = self.client.get(reverse('admin:index'))
        self.assertContains(resposta, 'Interessados esperando agência')
        self.assertContains(resposta, 'Ana Souza')
        self.assertContains(resposta, 'Últimos orçamentos')
        self.assertContains(resposta, 'Alfa Turismo')
        self.assertNotContains(resposta, 'reserva')

    def test_equipe_nao_ve_dados_de_cliente(self):
        self._entrar_no_painel(User.objects.create_user('equipe', 'e@x.com', SENHA,
                                                        is_staff=True))
        resposta = self.client.get(reverse('admin:index'))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, 'Ana Souza')
        self.assertNotContains(resposta, 'Últimos orçamentos')
