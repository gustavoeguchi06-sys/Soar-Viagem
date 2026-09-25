"""Páginas públicas do Blog Soar: o índice de artigos e cada artigo."""
from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Artigo, Categoria, Inscricao

POR_PAGINA = 8
TAMANHO_MAXIMO_BUSCA = 80


def _lateral():
    """O que a barra lateral mostra nas duas páginas."""
    no_ar = Artigo.objects.no_ar()
    categorias = Categoria.objects.annotate(total=Count('artigos', filter=Q(
        artigos__publicado=True, artigos__data_publicacao__lte=timezone.localdate()),
    )).order_by('ordem', 'nome')   # consulta com contagem ignora a ordem padrão do modelo
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
    # Na ordem da vitrine: "anterior" é o que vem logo depois (mais antigo) e
    # "próximo" o que vem logo antes (mais novo). Mesma data: vale a ordem de cadastro.
    anterior = no_ar.filter(Q(data_publicacao__lt=artigo.data_publicacao)
                            | Q(data_publicacao=artigo.data_publicacao, pk__gt=artigo.pk)
                            ).order_by('-data_publicacao', 'pk').first()
    proximo = no_ar.filter(Q(data_publicacao__gt=artigo.data_publicacao)
                           | Q(data_publicacao=artigo.data_publicacao, pk__lt=artigo.pk)
                           ).order_by('data_publicacao', '-pk').first()

    return render(request, 'blog/artigo.html', {
        'artigo': artigo,
        'secoes': artigo.secoes.all(),
        'atracoes': artigo.atracoes.all(),
        'previa': previa,
        'anterior': anterior,
        'proximo': proximo,
        **_lateral(),
    })


class _EmailForm(forms.Form):
    email = forms.EmailField(max_length=254)


@require_POST
def inscrever(request):
    """Recebe o e-mail dos formulários de newsletter do blog."""
    voltar = request.POST.get('voltar') or ''
    if not url_has_allowed_host_and_scheme(voltar, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        voltar = ''
    voltar = voltar or '/blog/'

    form = _EmailForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Esse e-mail não parece certo. Confira e tente de novo.')
        return redirect(voltar)

    email = form.cleaned_data['email'].strip().lower()
    _, nova = Inscricao.objects.get_or_create(email=email, defaults={'origem': voltar[:120]})
    if nova:
        messages.success(request, 'Pronto! Você vai receber as novidades da Soar nesse e-mail.')
    else:
        messages.info(request, 'Esse e-mail já recebe as novidades da Soar.')
    return redirect(voltar)
