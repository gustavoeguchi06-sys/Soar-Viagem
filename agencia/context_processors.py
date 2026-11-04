"""O pop-up de aviso aos agentes.

Aparece para o agente aprovado em qualquer página do site até ele fechar no X
(que grava na sessão; ver views.fechar_aviso). Ao sair e entrar de novo, a
sessão é outra e o pop-up volta. Não depende do momento do login: quem já
estava logado quando o aviso foi ligado também vê.
"""
from .apps import AVISO_FECHADO


def aviso_agente(request):
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    agencia = getattr(usuario, 'agente', None)
    if agencia is None or not agencia.aprovado:
        return {}
    from .models import AvisoAgente

    aviso = AvisoAgente.vigente()
    if aviso is None or request.session.get(AVISO_FECHADO) == aviso.pk:
        return {}
    return {'aviso_agente': aviso}
