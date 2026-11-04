"""Tira a marca do pop-up de aviso só quando ele foi entregue numa página."""
from .apps import AVISO_PENDENTE

MARCA_DO_POPUP = b'id="avisoAgente"'


class AvisoAgenteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resposta = self.get_response(request)
        sessao = getattr(request, 'session', None)
        if (sessao is not None and sessao.get(AVISO_PENDENTE)
                and resposta.status_code == 200
                and resposta.get('Content-Type', '').startswith('text/html')
                and not getattr(resposta, 'streaming', False)
                and MARCA_DO_POPUP in resposta.content):
            del sessao[AVISO_PENDENTE]
        return resposta
