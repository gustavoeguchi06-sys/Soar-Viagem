from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from urllib.parse import urlencode

from .conteudo import montar_viagem
from .inicio import montar_inicio
from .models import MESES, Destino, Saida

# Uma busca útil cabe numa linha. Acima disso é só custo: o filtro varre a
# tabela inteira comparando substring em três colunas.
TAMANHO_MAXIMO_BUSCA = 80
POR_PAGINA = 12


def home(request):
    """Página inicial (o conteúdo é montado em destinations/inicio.py)."""
    return render(request, 'destinations/home.html', {'inicio': montar_inicio()})


def lista_destinos(request):
    """Lista de todos os destinos, com busca e filtro por região."""
    destinos = Destino.objects.all()

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


def soar_60(request):
    """A página do programa Soar 60+.

    O botão da home ia direto para o WhatsApp: a pessoa era jogada numa
    conversa sem ter visto viagem nenhuma, e tinha que perguntar o que existe
    para só então decidir. Aqui ela conhece o programa e as viagens primeiro; o
    WhatsApp fica no fim, para quando ela realmente quiser reservar.

    Enquanto nenhuma viagem estiver marcada como 60+ no painel, a página mostra
    o catálogo inteiro — melhor do que uma página vazia, e é verdade: toda
    viagem da Soar pode ser feita no ritmo 60+, é só combinar.
    """
    viagens = Destino.objects.filter(soar_60=True)
    escolhidas = viagens.exists()
    if not escolhidas:
        viagens = Destino.objects.all()

    return render(request, 'destinations/soar_60.html', {
        'viagens': viagens[:POR_PAGINA],
        'escolhidas': escolhidas,
    })


def detalhe_destino(request, slug):
    """Detalhe do destino: galeria, hospedagens e avaliações.

    As avaliações são só as que o Tuca cadastra e publica no painel: sem conta
    de cliente no site, não tem mais formulário de avaliar aqui.
    """
    destino = get_object_or_404(
        Destino.objects.prefetch_related('imagens', 'hospedagens'),
        slug=slug,
    )
    avaliacoes = list(destino.avaliacoes.publicadas())
    return render(request, 'destinations/detalhe.html', {
        'destino': destino,
        'hospedagens': destino.hospedagens.all(),
        'avaliacoes': avaliacoes,
        'viagem': montar_viagem(destino, avaliacoes),
    })


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
