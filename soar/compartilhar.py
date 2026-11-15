"""Etiquetas de compartilhamento (Open Graph) para o link aparecer com foto,
título e descrição no WhatsApp, Instagram, Facebook etc.

Sem elas o WhatsApp adivinha uma imagem qualquer da página e mostra só uma
miniatura pequena. Com og:image grande (deitada), ele mostra a foto em cima.
Usado pela página da viagem e pelo artigo do blog; as outras páginas ficam com
o padrão de templates/partials/_compartilhar.html.
"""
FORMATOS_ACEITOS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')


def _absoluta(request, url):
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    return request.build_absolute_uri(url)


def primeira_foto(*urls):
    """A primeira que o WhatsApp mostra (SVG das ilustrações de exemplo não)."""
    for url in urls:
        if url and url.split('?')[0].lower().endswith(FORMATOS_ACEITOS):
            return url
    return ''


def dados(request, titulo, descricao='', imagem='', tipo='website'):
    descricao = ' '.join((descricao or '').split())
    if len(descricao) > 200:
        descricao = descricao[:197].rsplit(' ', 1)[0] + '...'
    return {
        'titulo': titulo,
        'descricao': descricao,
        'imagem': _absoluta(request, imagem),
        'url': request.build_absolute_uri(request.path),
        'tipo': tipo,
    }
