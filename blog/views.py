"""Páginas públicas do Blog Soar: o índice de artigos e cada artigo."""
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Artigo, Categoria

POR_PAGINA = 8
TAMANHO_MAXIMO_BUSCA = 80


def _lateral():
    """O que a barra lateral mostra nas duas páginas."""
    no_ar = Artigo.objects.no_ar()
    categorias = Categoria.objects.annotate(total=Count('artigos', filter=Q(
        artigos__publicado=True, artigos__data_publicacao__lte=timezone.localdate()),
    )).filter(total__gt=0)
    return {
        'categorias': categorias,
        'total_no_ar': no_ar.count(),
        'mais_lidos': no_ar.order_by('-leituras', '-data_publicacao')[:5],
    }


def indice(request):
    artigos = Artigo.objects.no_ar().select_related('categoria')

    busca = request.GET.get('q', '').strip()[:TAMANHO_MAXIMO_BUSCA]
    if busca:
        artigos = artigos.filter(Q(titulo__icontains=busca) | Q(resumo__icontains=busca)
                                 | Q(introducao__icontains=busca))

    categoria = None
    slug_categoria = request.GET.get('categoria', '')
    if slug_categoria:
        categoria = Categoria.objects.filter(slug=slug_categoria).first()
        if categoria:
            artigos = artigos.filter(categoria=categoria)

    # O destaque abre a primeira página, grande, só na vitrine sem filtro.
    destaque = None
    numero = request.GET.get('pagina', '1')
    if not busca and not categoria and numero in ('', '1'):
        destaque = artigos.filter(destaque=True).first()
    if destaque:
        artigos = artigos.exclude(pk=destaque.pk)

    pagina = Paginator(artigos, POR_PAGINA).get_page(numero)

    return render(request, 'blog/indice.html', {
        'destaque': destaque,
        'pagina': pagina,
        'busca': busca,
        'categoria_ativa': categoria,
        **_lateral(),
    })


def artigo(request, slug):
    artigo = get_object_or_404(
        Artigo.objects.select_related('categoria', 'destino')
                      .prefetch_related('secoes', 'atracoes'),
        slug=slug)

    # Rascunho e agendado só o dono vê, para conferir antes de ir ao ar.
    previa = not artigo.no_ar
    if previa and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404('Artigo não encontrado.')

    if not previa and not request.user.is_staff:
        Artigo.objects.filter(pk=artigo.pk).update(leituras=F('leituras') + 1)

    no_ar = Artigo.objects.no_ar()
    anterior = no_ar.filter(Q(data_publicacao__lt=artigo.data_publicacao)
                            | Q(data_publicacao=artigo.data_publicacao, pk__lt=artigo.pk)
                            ).order_by('-data_publicacao', '-pk').first()
    proximo = no_ar.filter(Q(data_publicacao__gt=artigo.data_publicacao)
                           | Q(data_publicacao=artigo.data_publicacao, pk__gt=artigo.pk)
                           ).order_by('data_publicacao', 'pk').first()

    return render(request, 'blog/artigo.html', {
        'artigo': artigo,
        'secoes': artigo.secoes.all(),
        'atracoes': artigo.atracoes.all(),
        'previa': previa,
        'anterior': anterior,
        'proximo': proximo,
        **_lateral(),
    })
