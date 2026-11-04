"""O pop-up de aviso aos agentes: só logo depois do login (ver agencia/apps.py)."""
from .apps import AVISO_PENDENTE


def aviso_agente(request):
    sessao = getattr(request, 'session', None)
    if sessao is None or not sessao.get(AVISO_PENDENTE):
        return {}
    from .models import AvisoAgente

    aviso = AvisoAgente.vigente()
    if aviso is None:
        # nada no ar agora: não guarda a marca para um aviso ligado mais tarde
        del sessao[AVISO_PENDENTE]
        return {}
    return {'aviso_agente': aviso}
