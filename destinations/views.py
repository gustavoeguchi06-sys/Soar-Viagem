import logging

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from reviews.forms import AvaliacaoForm
from soar.seguranca import LIMITE_AVALIACAO, LIMITE_INTERESSE, ip_do_cliente

from .conteudo import montar_viagem
from .forms import InteresseForm
from .inicio import montar_inicio
from .models import MESES, Destino, PaginaSobre, PaginaSoar60, Saida, VideoSoar60

log = logging.getLogger('soar.seguranca')

# Uma busca útil cabe numa linha. Acima disso é só custo: o filtro varre a
# tabela inteira comparando substring em três colunas.
TAMANHO_MAXIMO_BUSCA = 80
POR_PAGINA = 12


def home(request):
    """Página inicial (o conteúdo é montado em destinations/inicio.py)."""
    return render(request, 'destinations/home.html', {'inicio': montar_inicio()})


def lista_destinos(request):
    """Lista de todos os destinos, com busca e filtro por região."""
    # o card usa fotos e avaliações: busca tudo junto, não uma consulta por card
    destinos = Destino.objects.prefetch_related('imagens', 'avaliacoes')

    busca = request.GET.get('q', '').strip()[:TAMANHO_MAXIMO_BUSCA]
    if busca:
        destinos = destinos.filter(
            Q(nome__icontains=busca) | Q(pais__icontains=busca) | Q(descricao__icontains=busca)
        )

    regiao = request.GET.get('regiao', '')
    # Só região que existe: valor inventado devolve a lista inteira sem
    # filtro nenhum, o que confunde mais do que ajuda.
    if regiao in dict(Destino.REGIOES):
        destinos = destinos.filter(regiao=regiao)
    else:
        regiao = ''

    # Filtros da busca da página inicial: mês da saída e estilo.
    filtros = []
    hoje = timezone.localdate()
    saidas = Saida.objects.filter(data_ida__gte=hoje)
    # "2027-03" (mês e ano, como vem da página inicial) ou só "3" (qualquer ano)
    mes = request.GET.get('mes', '').strip()
    ano, _, numero = mes.rpartition('-')
    if numero.isdigit() and 1 <= int(numero) <= 12 and (not ano or (ano.isdigit() and len(ano) == 4)):
        saidas = saidas.filter(data_ida__month=int(numero))
        if ano:
            saidas = saidas.filter(data_ida__year=int(ano))
            filtros.append('saídas em {} de {}'.format(MESES[int(numero)].lower(), ano))
        else:
            filtros.append('saídas em {}'.format(MESES[int(numero)].lower()))
    else:
        mes = ''
    if mes:
        destinos = destinos.filter(pk__in=saidas.values('destino'))
    estilo = request.GET.get('estilo', '').strip()[:40]
    if estilo:
        destinos = destinos.filter(selo__iexact=estilo)
        filtros.append('estilo {}'.format(estilo.lower()))

    # os filtros vão junto nos links de página e de região
    mantidos = {k: v for k, v in (('q', busca), ('mes', mes), ('estilo', estilo)) if v}

    # Paginação: sem ela, uma busca ampla renderiza o catálogo todo de uma vez.
    pagina = Paginator(destinos, POR_PAGINA).get_page(request.GET.get('pagina'))

    return render(request, 'destinations/lista.html', {
        'destinos': pagina,
        'pagina': pagina,
        'busca': busca,
        'regiao_ativa': regiao,
        'regioes': Destino.REGIOES,
        'filtros': filtros,
        'qs_filtros': urlencode(mantidos),
    })


def sobre(request):
    """A página "Sobre a Soar": tudo nela é editado no painel (aba Sobre a Soar)."""
    pagina = PaginaSobre.atual()
    return render(request, 'destinations/sobre.html', {
        'pagina': pagina,
        'diferenciais': pagina.diferenciais.all(),
        'numeros': pagina.numeros.all(),
        'fotos': pagina.fotos.all(),
    })


def soar_60(request):
    """A página do programa Soar 60+.

    O botão da home ia direto para o WhatsApp: a pessoa era jogada numa
    conversa sem ter visto viagem nenhuma, e tinha que perguntar o que existe
    para só então decidir. Aqui ela conhece o programa e as viagens primeiro, e
    reserva pela página da viagem que escolher.

    Enquanto nenhuma viagem estiver marcada como 60+ no painel, a página mostra
    o catálogo inteiro — melhor do que uma página vazia, e é verdade: toda
    viagem da Soar pode ser feita no ritmo 60+, é só combinar.
    """
    pagina = PaginaSoar60.atual()
    viagens = Destino.objects.filter(soar_60=True).prefetch_related('imagens', 'avaliacoes')
    escolhidas = viagens.exists()
    if not escolhidas:
        viagens = Destino.objects.prefetch_related('imagens', 'avaliacoes')

    return render(request, 'destinations/soar_60.html', {
        'viagens': viagens[:POR_PAGINA],
        'escolhidas': escolhidas,
        'pagina': pagina,
        'itens': pagina.itens.all(),
        'passos': pagina.passos.all(),
        'perguntas': pagina.perguntas.all(),
        'videos': VideoSoar60.objects.filter(ativo=True),
    })


def detalhe_destino(request, slug):
    """Detalhe do destino: galeria, hospedagens e avaliações.

    As avaliações são só as que o Tuca cadastra e publica no painel: sem conta
    de cliente no site, não tem mais formulário de avaliar aqui.
    """
    destino = get_object_or_404(
        Destino.objects.prefetch_related('imagens', 'hospedagens', 'videos', 'precos', 'servicos'),
        slug=slug,
    )
    return pagina_da_viagem(request, destino, enviado=request.GET.get('enviado') == '1',
                            avaliacao_enviada=request.GET.get('avaliacao') == '1')


def pagina_da_viagem(request, destino, form_interesse=None, form_orcamento=None, enviado=False,
                     form_avaliacao=None, avaliacao_enviada=False):
    """Monta a página da viagem.

    Para a agência aprovada, o card traz o formulário de orçamento (agencia/views.py
    recebe o envio) e, logo depois de criar, o resumo do orçamento com o aviso.
    """
    avaliacoes = list(destino.avaliacoes.publicadas())
    viagem = montar_viagem(destino, avaliacoes)
    contexto = {
        'destino': destino,
        'hospedagens': destino.hospedagens.all(),
        'avaliacoes': avaliacoes,
        'viagem': viagem,
        'form_interesse': form_interesse or InteresseForm(),
        'interesse_enviado': enviado,
        # avaliação do visitante: com erro, o pop-up já abre mostrando o que corrigir
        'form_avaliacao': form_avaliacao or AvaliacaoForm(),
        'avaliacao_com_erro': form_avaliacao is not None,
        'avaliacao_enviada': avaliacao_enviada,
        # o que fica marcado no card: o que veio no envio, o link do calendário
        # (?saida=) ou o padrão da viagem
        'saida_marcada': next((str(s['id']) for s in viagem['saidas'] if s.get('padrao')), ''),
        'acomodacao_marcada': 'casal',
    }

    # veio de um card de saída da página inicial ou do calendário (?saida=12)
    pedida = request.GET.get('saida', '')
    if any(str(s['id']) == pedida and not s['esgotada'] for s in viagem['saidas']):
        contexto['saida_marcada'] = pedida

    agencia = getattr(request.user, 'agente', None)
    if agencia is not None and agencia.aprovado:
        from agencia.forms import OrcamentoViagemForm
        from agencia.models import AVISO

        if form_orcamento is None:
            inicial = {'pessoas': 2}
            pk = request.GET.get('interessado', '')
            interessado = agencia.interessados.filter(pk=pk).first() if pk.isdigit() else None
            if interessado:
                inicial.update(cliente_nome=interessado.nome,
                               cliente_telefone=interessado.whatsapp)
            form_orcamento = OrcamentoViagemForm(destino=destino, initial=inicial)
            saida = request.GET.get('saida', '')
            if saida in dict(form_orcamento.fields['saida'].choices) and saida:
                contexto['saida_marcada'] = saida
        else:
            contexto['saida_marcada'] = form_orcamento.data.get('saida', '')
            contexto['acomodacao_marcada'] = form_orcamento.data.get('acomodacao', '')

        pk = request.GET.get('orcamento', '')
        contexto.update(
            form_orcamento=form_orcamento,
            orcamento_criado=(agencia.orcamentos.filter(pk=pk, destino=destino).first()
                              if pk.isdigit() else None),
            aviso_orcamento=AVISO,
        )

    return render(request, 'destinations/detalhe.html', contexto)


@require_POST
def interesse(request, slug):
    """Recebe o "Saiba mais" de quem não tem login e responde que a Soar é B2B.

    O contato fica no painel (Interessados) para o dono encaminhar a uma
    agência parceira. Cada IP tem um limite por hora, para ninguém encher a
    lista com pedido falso.
    """
    destino = get_object_or_404(Destino, slug=slug)
    form = InteresseForm(request.POST)
    if not form.is_valid():
        return pagina_da_viagem(request, destino, form_interesse=form)

    if LIMITE_INTERESSE.estourou(request):
        log.warning('saiba mais bloqueado por limite: ip=%s', ip_do_cliente(request))
        messages.error(request, 'Muitos pedidos daqui agora há pouco. Tente de novo mais tarde.')
        return redirect(destino.get_absolute_url() + '#reservar')
    LIMITE_INTERESSE.registrar(request)

    interessado = form.save(commit=False)
    interessado.destino = destino
    interessado.save()
    return redirect(destino.get_absolute_url() + '?enviado=1#reservar')


@require_POST
def avaliar(request, slug):
    """Recebe a avaliação de um visitante. Entra na fila: o dono aprova no painel.

    Sem conta, qualquer pessoa pode avaliar; por isso o IP fica guardado (6
    meses, para apurar abuso), cada IP tem um limite por hora e um campo
    escondido pega robô de spam.
    """
    destino = get_object_or_404(Destino, slug=slug)
    form = AvaliacaoForm(request.POST, request.FILES)
    if not form.is_valid():
        return pagina_da_viagem(request, destino, form_avaliacao=form)

    if form.eh_robo():
        # finge que deu certo: o robô não aprende que foi barrado
        log.warning('avaliacao de robo descartada: ip=%s', ip_do_cliente(request))
        return redirect(destino.get_absolute_url() + '?avaliacao=1#avaliacoes')
    if LIMITE_AVALIACAO.estourou(request):
        log.warning('avaliacao bloqueada por limite: ip=%s', ip_do_cliente(request))
        messages.error(request, 'Muitas avaliações daqui agora há pouco. Tente de novo mais tarde.')
        return redirect(destino.get_absolute_url() + '#avaliacoes')
    LIMITE_AVALIACAO.registrar(request)

    avaliacao = form.save(commit=False)
    avaliacao.destino = destino
    avaliacao.ip = ip_do_cliente(request)
    avaliacao.publicada = False
    avaliacao.save()
    log.info('avaliacao recebida: destino=%s avaliacao=%s ip=%s', destino.slug, avaliacao.pk,
             ip_do_cliente(request))
    return redirect(destino.get_absolute_url() + '?avaliacao=1#avaliacoes')


def calendario(request):
    """Todas as saídas que ainda vão acontecer, de todos os destinos, mês a mês."""
    saidas = (Saida.objects.filter(data_ida__gte=timezone.localdate())
              .select_related('destino').order_by('data_ida', 'destino__nome'))
    meses = []
    for saida in saidas:
        chave = (saida.data_ida.year, saida.data_ida.month)
        if not meses or meses[-1]['chave'] != chave:
            meses.append({'chave': chave, 'nome': f'{MESES[chave[1]]} de {chave[0]}', 'saidas': []})
        meses[-1]['saidas'].append(saida)
    return render(request, 'destinations/calendario.html', {'meses': meses})
