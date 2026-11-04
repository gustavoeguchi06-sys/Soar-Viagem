"""O pop-up de aviso aos agentes, uma vez por login (ver agencia/apps.py)."""
from .apps import AVISO_PENDENTE


def aviso_agente(request):
    sessao = getattr(request, 'session', None)
    if sessao is None or not sessao.get(AVISO_PENDENTE):
        return {}
    from .models import AvisoAgente

    del sessao[AVISO_PENDENTE]
    aviso = AvisoAgente.vigente()
    return {'aviso_agente': aviso} if aviso else {}
