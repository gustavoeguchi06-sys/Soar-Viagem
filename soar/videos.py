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


def validar_video(arquivo):
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
