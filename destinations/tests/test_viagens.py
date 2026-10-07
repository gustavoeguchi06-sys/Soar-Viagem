"""Várias datas de saída por destino."""
import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone


from ..models import Destino, Saida


class SaidasTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                              preco_base=3000)
        hoje = timezone.localdate()
        self.passada = Saida.objects.create(destino=self.destino, vagas=5,
                                            data_ida=hoje - timedelta(days=30),
                                            data_volta=hoje - timedelta(days=25))
        self.lotada = Saida.objects.create(destino=self.destino, vagas=0,
                                           data_ida=hoje + timedelta(days=20),
                                           data_volta=hoje + timedelta(days=24))
        self.livre = Saida.objects.create(destino=self.destino, vagas=8,
                                          data_ida=hoje + timedelta(days=60),
                                          data_volta=hoje + timedelta(days=65))
        self.outra = Saida.objects.create(destino=self.destino, vagas=None,
                                          data_ida=hoje + timedelta(days=120),
                                          data_volta=hoje + timedelta(days=125))

    def test_pagina_lista_todas_as_saidas_futuras(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        html = resposta.content.decode()
        self.assertContains(resposta, 'Próximas saídas')
        for saida in (self.lotada, self.livre, self.outra):
            self.assertIn(saida.texto, html)
        self.assertNotIn(self.passada.texto, html)
        self.assertContains(resposta, 'Esgotada')
        self.assertContains(resposta, '8 vagas')
        self.assertContains(resposta, 'Consulte')

    def test_capa_mostra_a_primeira_saida_com_vaga(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertEqual(resposta.context['viagem']['periodo'], self.livre.textos['periodo'])

    def test_rotas_antigas_de_reserva_do_cliente_nao_existem_mais(self):
        # Antes de a venda passar para as agências, o cliente reservava aqui.
        # Sem conta de cliente, a rota só servia para alguém criar pedido
        # digitando o endereço direto.
        cliente = User.objects.create_user('cli', 'cli@exemplo.com', 'senha-boa-123')
        self.client.force_login(cliente)
        self.assertEqual(self.client.get('/reservar/bonito/').status_code, 404)
        self.assertEqual(self.client.post('/reservar/bonito/', {'acomodacao': 'casal'}).status_code,
                         404)
        self.assertEqual(self.client.post('/reservas/1/cancelar/').status_code, 404)

    def test_saida_esgotada_nao_entra_no_orcamento(self):
        from agencia.forms import OrcamentoViagemForm
        form = OrcamentoViagemForm({'cliente_nome': 'Bruno', 'cliente_email': 'b@gmail.com',
                                    'acomodacao': 'casal', 'pessoas': 2,
                                    'saida': self.lotada.pk}, destino=self.destino)
        self.assertFalse(form.is_valid())
        self.assertIn('saida', form.errors)
        self.assertNotIn(str(self.lotada.pk), dict(form.fields['saida'].choices))
        self.assertIn(str(self.livre.pk), dict(form.fields['saida'].choices))

    def test_sem_saidas_cadastradas_mantem_o_texto_antigo(self):
        Saida.objects.all().delete()
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Próxima saída')
        self.assertContains(resposta, 'Vagas disponíveis')


class ServiceWorkerTests(TestCase):
    def test_sw_js_desinstala_o_worker_antigo(self):
        resposta = self.client.get('/sw.js')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('javascript', resposta['Content-Type'])
        self.assertIn('unregister', resposta.content.decode())
        self.assertEqual(resposta['Cache-Control'], 'no-store')


class PaginasDeErroTests(TestCase):
    def test_404_tem_a_cara_do_site(self):
        resposta = self.client.get('/pagina-que-nao-existe/')
        self.assertEqual(resposta.status_code, 404)
        self.assertContains(resposta, 'Essa página não existe', status_code=404)

    def test_500_renderiza_sem_request(self):
        from django.template.loader import render_to_string
        self.assertIn('Algo deu errado aqui', render_to_string('500.html'))


class TopoTests(TestCase):
    def test_visitante_sem_botao_verde_e_sem_comentario_vazando(self):
        html = self.client.get('/').content.decode()
        self.assertNotIn('btn--reservar', html)
        self.assertNotIn('{#', html)


class RecomendacoesTests(TestCase):
    def test_recomendacoes_vem_depois_do_faq(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        html = self.client.get(destino.get_absolute_url()).content.decode()
        self.assertLess(html.index('id="faq"'), html.index('id="avaliacoes"'))
        # sem avaliação publicada: o aviso aparece, o carrossel vazio não
        self.assertIn('ainda não tem avaliações publicadas', html)
        self.assertNotIn('id="trilhoDepo"', html)


class CartaoDestinoTests(TestCase):
    def test_destino_sem_foto_usa_ilustracao(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.assertTrue(destino.capa_card.endswith('.svg'))
        resposta = self.client.get('/destinos/')
        self.assertNotContains(resposta, '🏝')


class CriancaAdicionalTests(TestCase):
    def test_crianca_e_adicional_sob_consulta(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         preco_base=3000)
        resposta = self.client.get(destino.get_absolute_url())
        self.assertContains(resposta, 'Crianças até 8 anos (CHD)')
        self.assertContains(resposta, 'Viajam acompanhadas de um adulto')
        self.assertNotContains(resposta, 'Grátis')
        # não é uma acomodação que dê para marcar sozinha
        self.assertNotContains(resposta, 'value="crianca"')
        # o campo de idades é só para a agência, que monta o orçamento
        self.assertNotContains(resposta, 'name="idades_criancas"')
        self.assertNotContains(resposta, 'Falar com o agente')


class FuncionalidadesTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                              preco_base=3000)
        hoje = timezone.localdate()
        self.saida = Saida.objects.create(destino=self.destino, vagas=5,
                                          data_ida=hoje + timedelta(days=30),
                                          data_volta=hoje + timedelta(days=34))

    def test_sem_avaliacoes_nao_inventa_nota(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Ainda sem avaliações')
        self.assertNotContains(resposta, '87 avaliações')

    def test_calendario_lista_as_saidas(self):
        resposta = self.client.get('/calendario/')
        self.assertContains(resposta, 'Bonito')
        self.assertContains(resposta, self.saida.texto)
        self.assertContains(resposta, 'Ver viagem')
        self.assertNotContains(resposta, '/reservar/bonito/')

    def test_newsletter_grava_o_email(self):
        from blog.models import Inscricao
        resposta = self.client.post('/blog/novidades/', {'email': 'Ana@Exemplo.com',
                                                         'voltar': '/blog/'})
        self.assertRedirects(resposta, '/blog/', fetch_redirect_response=False)
        self.assertTrue(Inscricao.objects.filter(email='ana@exemplo.com').exists())
        self.client.post('/blog/novidades/', {'email': 'ana@exemplo.com'})
        self.assertEqual(Inscricao.objects.count(), 1)
        resposta = self.client.post('/blog/novidades/', {'email': 'x',
                                                         'voltar': 'https://golpe.com/'})
        self.assertRedirects(resposta, '/blog/', fetch_redirect_response=False)


class ExemplosPorRegiaoTests(TestCase):
    def test_um_exemplo_por_regiao_sem_duplicar(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('criar_exemplos_regioes', stdout=StringIO())
        call_command('criar_exemplos_regioes', stdout=StringIO())
        regioes = set(Destino.objects.values_list('regiao', flat=True))
        self.assertEqual(regioes, {'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'})
        self.assertEqual(Destino.objects.count(), 4)
        resposta = self.client.get('/destinos/?regiao=Sul')
        self.assertContains(resposta, 'Cânions do Sul')
        pagina = self.client.get('/destinos/lencois-maranhenses/')
        self.assertContains(pagina, 'Lagoa Bonita')
        self.assertContains(pagina, 'Maranhão')


class PaginaInicialTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        self.d = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                        preco_base=3690, regiao='Centro-Oeste', selo='Natureza',
                                        estado='Mato Grosso do Sul')
        hoje = timezone.localdate()
        self.s = Saida.objects.create(destino=self.d, vagas=3, data_ida=hoje + timedelta(days=40),
                                      data_volta=hoje + timedelta(days=44))

    def test_pagina_inicial_mostra_as_secoes(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        for texto in ['Muito além do destino, uma Experiência!', 'Encontre a viagem perfeita',
                      'Próximas experiências', 'Destinos mais amados', 'Por que viajar com a Soar?',
                      'Viajar não tem idade.', '@operadorasoar</a></h2>', 'Pronto para sua próxima aventura?',
                      'Últimas vagas', 'R$ 3.690', 'Natureza']:
            self.assertContains(r, texto)

    def test_busca_por_destino_mes_e_estilo(self):
        mes = self.s.data_ida.month
        outro = mes % 12 + 1
        pagina = self.client.get('/')
        self.assertContains(pagina, '<option value="Bonito">Bonito</option>', html=True)
        self.assertNotContains(pagina, 'name="duracao"')
        self.assertContains(self.client.get(f'/destinos/?q=Bonito&mes={mes}&estilo=Natureza'), 'Bonito')
        self.assertNotContains(self.client.get(f'/destinos/?mes={outro}'), '/destinos/bonito/')
        self.assertNotContains(self.client.get('/destinos/?estilo=Cultura'), '/destinos/bonito/')

    def test_busca_so_com_destinos_e_meses_que_tem_saida(self):
        from ..models import MESES
        Destino.objects.create(nome='Sem Data', slug='sem-data', descricao='x')
        ida = self.s.data_ida
        valor = '{}-{:02d}'.format(ida.year, ida.month)
        pagina = self.client.get('/')
        self.assertNotContains(pagina, '<option value="Sem Data">')
        self.assertContains(pagina, '{} de {}</option>'.format(MESES[ida.month], ida.year))
        self.assertContains(pagina, 'value="{}" data-destinos="Bonito"'.format(valor))
        self.assertContains(self.client.get(f'/destinos/?mes={valor}'), '/destinos/bonito/')
        self.assertNotContains(self.client.get('/destinos/?mes={}-{:02d}'.format(ida.year + 1, ida.month)),
                               '/destinos/bonito/')


# O que se testa aqui é o conteúdo do painel; o código do celular tem os
# testes dele em contas/tests.py (DoisFatoresTests).
@override_settings(DOIS_FATORES_EQUIPE=False)
class SemPrecoTests(TestCase):
    def test_destino_sem_preco_mostra_sob_consulta(self):
        d = Destino.objects.create(nome='Caraça', slug='caraca', descricao='Santuário.')
        r = self.client.get(d.get_absolute_url())
        self.assertContains(r, 'Sob consulta')
        self.assertNotContains(r, '3.588')

    def test_hospedagem_fora_do_menu_e_dentro_do_destino(self):
        from django.contrib.auth.models import User
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        d = Destino.objects.create(nome='Caraça', slug='caraca', descricao='Santuário.')
        tela = self.client.get(f'/painel/destinations/destino/{d.pk}/change/')
        self.assertContains(tela, 'Hospedagem do pacote')
        self.assertNotContains(self.client.get('/painel/'), '/painel/destinations/hospedagem/')


class SaibaMaisTests(TestCase):
    """Sem login, o card da viagem tem "Saiba mais": nome, e-mail, WhatsApp e CEP."""

    MENSAGEM = 'A Operadora Soar é uma empresa B2B'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.url = reverse('destinations:interesse', args=['bonito'])

    def dados(self, **extra):
        return {'nome': 'Ana Souza', 'email': 'ana@exemplo.com',
                'whatsapp': '11988887777', 'cep': '01310100', **extra}

    def test_sem_login_aparece_saiba_mais(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Saiba mais</summary>')
        self.assertContains(resposta, 'name="cep"')
        self.assertNotContains(resposta, 'Criar orçamento')
        self.assertNotContains(resposta, self.MENSAGEM)

    def test_enviar_guarda_os_dados_e_mostra_a_mensagem(self):
        from ..models import Interessado
        resposta = self.client.post(self.url, self.dados(), follow=True)
        self.assertContains(resposta, self.MENSAGEM)
        self.assertContains(resposta, 'agência conveniada mais próxima de você')
        self.assertContains(resposta, 'Seja muito bem-vindo(a) à Operadora Soar!')
        # aparece como pop-up, que abre sozinho ao carregar a página
        self.assertContains(resposta, 'id="interessePopup" data-popup data-abrir-ja open')
        self.assertNotContains(resposta, 'Saiba mais</summary>')
        pedido = Interessado.objects.get()
        self.assertEqual((pedido.destino, pedido.whatsapp, pedido.cep),
                         (self.destino, '(11) 98888-7777', '01310-100'))

    def test_vai_junto_a_data_e_os_quartos(self):
        from ..models import Interessado, PrecoQuarto, Saida
        PrecoQuarto.objects.create(destino=self.destino, tipo='duplo', preco=3000)
        PrecoQuarto.objects.create(destino=self.destino, tipo='triplo', preco=2800)
        hoje = timezone.localdate()
        saida = Saida.objects.create(destino=self.destino, data_ida=hoje + timedelta(days=30),
                                     data_volta=hoje + timedelta(days=34), quartos_triplo=1)
        pagina = self.client.get(self.destino.get_absolute_url()).content.decode()
        self.assertIn('data-quartos-orcamento', pagina)
        self.assertIn('name="quartos_triplo"', pagina)
        # passou da lotação: volta com o erro e não grava
        resposta = self.client.post(self.url, self.dados(saida=saida.pk, quartos_triplo=1,
                                                         pessoas_triplo=4))
        self.assertContains(resposta, 'no máximo 3.')
        self.assertFalse(Interessado.objects.exists())
        self.client.post(self.url, self.dados(saida=saida.pk, quartos_duplo=2, pessoas_duplo=3,
                                              quartos_triplo=1, pessoas_triplo=2))
        pedido = Interessado.objects.get()
        self.assertEqual(pedido.saida_texto, saida.texto)
        self.assertEqual(pedido.pessoas, 5)
        self.assertEqual(pedido.quartos_texto,
                         '2 quartos Duplo (Twin), 3 pessoas; 1 quarto Triplo, 2 pessoas')

    def test_campo_errado_volta_com_o_erro_e_nao_grava(self):
        from ..models import Interessado
        resposta = self.client.post(self.url, self.dados(cep='123'))
        self.assertContains(resposta, 'O CEP tem 8 números')
        self.assertContains(resposta, '<details class="interesse" open>')
        self.assertFalse(Interessado.objects.exists())

    def test_tem_limite_por_hora(self):
        from soar.seguranca import LIMITE_INTERESSE
        from ..models import Interessado
        for _ in range(LIMITE_INTERESSE.tentativas + 2):
            self.client.post(self.url, self.dados())
        self.assertEqual(Interessado.objects.count(), LIMITE_INTERESSE.tentativas)


class InclusoTests(TestCase):
    """Incluso e não incluso em blocos separados na página da viagem."""

    def test_dois_blocos_separados(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         incluso='Transporte\nHospedagem',
                                         nao_incluso='Passagem aérea')
        resposta = self.client.get(destino.get_absolute_url())
        html = resposta.content.decode()
        incluso, nao = html.index('id="incluso"'), html.index('id="nao-incluso"')
        self.assertLess(html.index('Transporte'), nao)
        self.assertGreater(html.index('Passagem aérea'), nao)
        self.assertLess(incluso, nao)

    def test_sem_nao_incluso_nao_mostra_o_bloco(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         incluso='Transporte')
        resposta = self.client.get(destino.get_absolute_url())
        self.assertContains(resposta, 'id="incluso"')
        self.assertNotContains(resposta, 'id="nao-incluso"')


class InclusoNoPainelTests(TestCase):
    """No painel, "Incluso e não incluso" fica entre o roteiro e as perguntas frequentes."""

    def test_bloco_entre_roteiro_e_perguntas(self):
        from contas.dois_fatores import CHAVE_OK
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        sessao = self.client.session
        sessao[CHAVE_OK] = dono.pk
        sessao.save()
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        html = self.client.get(reverse('admin:destinations_destino_change',
                                       args=[destino.pk])).content.decode()
        # os títulos vêm com espaços e quebras de linha em volta
        html = re.sub(r'>\s+|\s+<', lambda m: m.group().strip(), html)
        self.assertEqual(html.count('>Incluso e não incluso<'), 1)
        self.assertEqual(html.count('name="nao_incluso"'), 1)
        roteiro = html.index('>Roteiro dia a dia<')
        incluso = html.index('>Incluso e não incluso<')
        perguntas = html.index('>Perguntas frequentes<')
        self.assertLess(roteiro, incluso)
        self.assertLess(incluso, perguntas)


class BannerAlbumHospedagemTests(TestCase):
    """Texto do banner editável, álbum em carrossel e botão das fotos da hospedagem."""

    def setUp(self):
        from contas.dois_fatores import CHAVE_OK
        self.dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(self.dono)
        sessao = self.client.session
        sessao[CHAVE_OK] = self.dono.pk
        sessao.save()

    def test_texto_do_banner_vem_do_painel(self):
        from ..models import TextoBanner
        self.assertContains(self.client.get('/'), 'Muito além do destino, uma Experiência!')
        texto = TextoBanner.para_editar()
        resposta = self.client.post(reverse('admin:destinations_textobanner_change', args=[texto.pk]),
                                    {'titulo': 'Viaje com quem entende', 'subtitulo': ''})
        self.assertRedirects(resposta, reverse('admin:destinations_slideinicio_changelist'))
        pagina = self.client.get('/')
        self.assertContains(pagina, '<h1>Viaje com quem entende</h1>', html=True)
        lista = self.client.get(reverse('admin:destinations_slideinicio_changelist'))
        self.assertContains(lista, 'Viaje com quem entende')
        self.assertContains(lista, 'Editar o texto')

    def test_album_abre_no_carrossel_e_nao_em_outra_aba(self):
        import shutil
        import tempfile
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image as Foto

        from ..models import ImagemDestino

        def jpg(nome):
            saida = BytesIO()
            Foto.new('RGB', (40, 30), (30, 120, 80)).save(saida, 'JPEG')
            return SimpleUploadedFile(nome, saida.getvalue(), content_type='image/jpeg')

        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        with override_settings(MEDIA_ROOT=pasta):
            destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
            ImagemDestino.objects.create(destino=destino, imagem=jpg('a.jpg'), legenda='Rio da Prata')
            ImagemDestino.objects.create(destino=destino, imagem=jpg('b.jpg'), legenda='Gruta')
            html = self.client.get(destino.get_absolute_url()).content.decode()
        grade = html[html.index('class="galeria-grade"'):html.index('id="album"')]
        self.assertNotIn('target="_blank"', grade)
        self.assertIn('data-legenda="Rio da Prata"', grade)
        self.assertEqual(grade.count('data-album='), 2)
        self.assertIn('<dialog class="album" id="album"', html)

    def test_botao_das_fotos_da_hospedagem_no_destino(self):
        from ..models import Hospedagem
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        hospedagem = Hospedagem.objects.create(destino=destino, nome='Pousada Bonito')
        tela = self.client.get(reverse('admin:destinations_destino_change', args=[destino.pk]))
        self.assertContains(tela, 'Adicionar ou ver as fotos da hospedagem')
        self.assertContains(tela, reverse('admin:destinations_hospedagem_change', args=[hospedagem.pk]))


class TopicosComTituloTests(TestCase):
    """Linha terminada em ":" vira título; as de baixo, tópicos dele."""

    TEXTO = ('Transporte:\n- Transfer aeroporto de Palmas x hospedagem\n- Jipes 4x4\n'
             'REFEIÇÕES:\n• 2 dia Café da manhã, Almoço e Jantar.\n'
             'Passeios:\nCanyon da Sussuapara;\nLagoa do Japonês;\nPedra Furada;')

    def test_agrupar(self):
        from ..conteudo import agrupar
        grupos = agrupar(['Seguro viagem', 'Passeios:', '- Taxa de entrada nos atrativos:',
                          '- Lagoa do Japonês;', '* Pedra Furada;', 'Hospedagem:'])
        self.assertEqual(grupos, [
            {'titulo': '', 'itens': ['Seguro viagem']},
            {'titulo': 'Passeios', 'itens': ['Taxa de entrada nos atrativos:', 'Lagoa do Japonês;',
                                             'Pedra Furada;']},
            {'titulo': 'Hospedagem', 'itens': []},
        ])

    def test_pagina_mostra_titulos_e_topicos(self):
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.',
                                         incluso=self.TEXTO, nao_incluso='Bebidas:\nRefrigerante')
        html = self.client.get(destino.get_absolute_url()).content.decode()
        self.assertIn('<h4 class="incl-grupo__titulo">Passeios</h4>', html)
        self.assertIn('<h4 class="incl-grupo__titulo">REFEIÇÕES</h4>', html)
        self.assertIn('<span>Transfer aeroporto de Palmas x hospedagem</span>', html)
        self.assertNotIn('<span>- Transfer', html)            # o "-" digitado sai
        self.assertNotIn('<span>Passeios:</span>', html)      # título não vira tópico
        self.assertIn('<h4 class="incl-grupo__titulo">Bebidas</h4>', html)

    def test_pdf_do_orcamento_tambem_agrupa(self):
        from agencia.pdf import _estilos, _pacote
        from ..conteudo import montar_viagem
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.',
                                         incluso=self.TEXTO)
        textos = []
        for f in _pacote(destino, montar_viagem(destino, []), _estilos()):
            for parte in getattr(f, '_content', [f]):
                if hasattr(parte, 'getPlainText'):
                    textos.append(parte.getPlainText())
        i = textos.index('Passeios')
        self.assertEqual(textos[i + 1], '- Canyon da Sussuapara;')


class NumeroDoDiaTests(TestCase):
    """Cada dia do roteiro mostra "Dia 1", "Dia 2"... pela ordem, sem repetir o do título."""

    def test_dias_numerados_pela_ordem(self):
        from ..models import DiaRoteiro
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        DiaRoteiro.objects.create(destino=destino, ordem=2, titulo='Pedra Furada', resumo='.')
        DiaRoteiro.objects.create(destino=destino, ordem=1, titulo='Dia 1: Recepção em Palmas',
                                  resumo='.')
        html = re.sub(r'\s+', ' ', self.client.get(destino.get_absolute_url()).content.decode())
        self.assertIn('<span class="dia__num">Dia 1</span> <span class="dia__texto"> '
                      '<b>Recepção em Palmas</b>', html)
        self.assertIn('<span class="dia__num">Dia 2</span> <span class="dia__texto"> '
                      '<b>Pedra Furada</b>', html)
        self.assertNotIn('Dia 1: Recepção', html)


class UmCardPorSaidaTests(TestCase):
    """Na página inicial, o mesmo pacote aparece uma vez para cada data de saída."""

    def test_um_card_por_data_em_ordem(self):
        hoje = timezone.localdate()
        jalapao = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        minas = Destino.objects.create(nome='Minas', slug='minas', descricao='Cidades.')
        breve = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        s1 = Saida.objects.create(destino=jalapao, data_ida=hoje + timedelta(days=60),
                                  data_volta=hoje + timedelta(days=65), vagas=10)
        Saida.objects.create(destino=minas, data_ida=hoje + timedelta(days=90),
                             data_volta=hoje + timedelta(days=93), vagas=3)
        s3 = Saida.objects.create(destino=jalapao, data_ida=hoje + timedelta(days=120),
                                  data_volta=hoje + timedelta(days=125), vagas=0)
        cards = self.client.get('/').context['inicio']['experiencias']
        self.assertEqual([(c['nome'], c['situacao']) for c in cards],
                         [('Jalapão', 'disponivel'), ('Minas', 'ultimas'),
                          ('Jalapão', 'esgotado'), ('Bonito', 'breve')])
        self.assertEqual(cards[0]['link'], '/destinos/jalapao/?saida={}#reservar'.format(s1.pk))
        self.assertEqual(cards[2]['proxima'], s3)
        self.assertEqual(cards[3]['link'], breve.get_absolute_url())

    def test_link_do_card_marca_a_data(self):
        hoje = timezone.localdate()
        destino = Destino.objects.create(nome='Jalapão', slug='jalapao', descricao='Dunas.')
        Saida.objects.create(destino=destino, data_ida=hoje + timedelta(days=60),
                             data_volta=hoje + timedelta(days=65), vagas=10)
        segunda = Saida.objects.create(destino=destino, data_ida=hoje + timedelta(days=90),
                                       data_volta=hoje + timedelta(days=95), vagas=10)
        resposta = self.client.get(destino.get_absolute_url(), {'saida': segunda.pk})
        self.assertEqual(resposta.context['saida_marcada'], str(segunda.pk))
        inventada = self.client.get(destino.get_absolute_url(), {'saida': '999'})
        self.assertNotEqual(inventada.context['saida_marcada'], '999')


class FaqComTopicosTests(TestCase):
    def test_linha_com_marcador_vira_topico(self):
        from ..conteudo import blocos_de_texto
        from ..models import PerguntaFrequente
        texto = ('Como o clima é quente, roupas leves:\n\nVestuário e Banho\n'
                 '• Roupas leves: shorts\n- Roupas de banho: 3 trocas\n\nCalçados\n• Sapatilha')
        self.assertEqual(blocos_de_texto(texto), [
            {'tipo': 'p', 'texto': 'Como o clima é quente, roupas leves:'},
            {'tipo': 'subtitulo', 'texto': 'Vestuário e Banho'},
            {'tipo': 'lista', 'itens': ['Roupas leves: shorts', 'Roupas de banho: 3 trocas']},
            {'tipo': 'subtitulo', 'texto': 'Calçados'},
            {'tipo': 'lista', 'itens': ['Sapatilha']},
        ])
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        PerguntaFrequente.objects.create(destino=destino, pergunta='Que roupa levar?',
                                         resposta=texto)
        html = self.client.get(destino.get_absolute_url()).content.decode()
        self.assertIn('<li>Roupas de banho: 3 trocas</li>', html)
        self.assertIn('<p class="faq-item__sub">Calçados</p>', html)
