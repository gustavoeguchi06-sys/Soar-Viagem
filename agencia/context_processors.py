"""O pop-up de aviso aos agentes: na página principal, logo depois do login
(ver agencia/apps.py). O login do agente aprovado já leva para lá."""
from .apps import AVISO_PENDENTE


def aviso_agente(request):
    sessao = getattr(request, 'session', None)
    if sessao is None or not sessao.get(AVISO_PENDENTE):
        return {}
    rota = getattr(request, 'resolver_match', None)
    if rota is None or rota.view_name != 'destinations:home':
        # só na página principal; a marca espera até ele chegar lá
        return {}
    from .models import AvisoAgente

    aviso = AvisoAgente.vigente()
    if aviso is None:
        # nada no ar agora: não guarda a marca para um aviso ligado mais tarde
        del sessao[AVISO_PENDENTE]
        return {}
    return {'aviso_agente': aviso}
