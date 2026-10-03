"""Vídeos enviados pelo painel: o que o site aceita.

Só a equipe envia vídeo (o limite maior de envio vale só para quem está logado
no painel, ver soar.middleware.LimiteDeEnvioMiddleware). Mesmo assim o arquivo
é conferido por dentro, e não só pelo nome: um arquivo qualquer renomeado para
.mp4 seria servido pelo site como se fosse vídeo.
"""
from django.conf import settings
from django.core.exceptions import ValidationError

EXTENSOES = ('mp4', 'm4v', 'webm')
AJUDA = ('MP4 ou WebM, até {} MB. Vídeos curtos (até 1 minuto) carregam mais rápido, '
         'principalmente no celular.')


def ajuda(extra=''):
    texto = AJUDA.format(settings.TAMANHO_MAXIMO_VIDEO // (1024 * 1024))
    return (extra + ' ' + texto).strip()


def _parece_video(cabeca):
    # MP4/M4V: a caixa "ftyp" logo no começo. WebM: o cabeçalho EBML.
    return cabeca[4:8] == b'ftyp' or cabeca[:4] == b'\x1a\x45\xdf\xa3'


def _ja_salvo(arquivo):
    """Arquivo que já está no armazenamento: foi conferido quando entrou.

    O Django roda os validadores de novo a cada salvar do registro; sem isto,
    um arquivo antigo (ou de antes desta regra) impediria salvar a viagem.
    """
    return getattr(arquivo, '_committed', False) is True


def validar_video(arquivo):
    if _ja_salvo(arquivo):
        return
    nome = (arquivo.name or '').lower()
    if not nome.endswith(tuple('.' + e for e in EXTENSOES)):
        raise ValidationError('Envie o vídeo em MP4 ou WebM.')
    limite = settings.TAMANHO_MAXIMO_VIDEO
    if arquivo.size > limite:
        raise ValidationError('Vídeo grande demais: o máximo é {} MB. Diminua a resolução ou '
                              'corte o vídeo e tente de novo.'.format(limite // (1024 * 1024)))
    posicao = arquivo.tell() if hasattr(arquivo, 'tell') else 0
    arquivo.seek(0)
    cabeca = arquivo.read(12)
    arquivo.seek(posicao)
    if not _parece_video(cabeca):
        raise ValidationError('Esse arquivo não é um vídeo MP4 ou WebM de verdade.')


# --------------------------------------------------------------------------- #
# Fotos
# --------------------------------------------------------------------------- #
# O ImageField do Django já confere se o arquivo é mesmo uma imagem (abre com o
# Pillow), mas aceita qualquer formato que o Pillow leia (TIFF, BMP, ICO...) e
# não tem teto de tamanho: no painel, o limite do envio é o dos vídeos.
EXTENSOES_FOTO = ('jpg', 'jpeg', 'png', 'webp', 'gif')


def validar_foto(arquivo):
    if _ja_salvo(arquivo):
        return
    nome = (arquivo.name or '').lower()
    if not nome.endswith(tuple('.' + e for e in EXTENSOES_FOTO)):
        raise ValidationError('Envie a foto em JPG, PNG, WebP ou GIF. Foto do iPhone (HEIC) '
                              'precisa ser convertida para JPG antes.')
    limite = settings.TAMANHO_MAXIMO_FOTO_PAINEL
    if arquivo.size > limite:
        raise ValidationError('Foto grande demais: o máximo é {} MB. Diminua a foto (ex.: no '
                              'squoosh.app) e envie de novo.'.format(limite // (1024 * 1024)))
