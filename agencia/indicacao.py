"""Link de indicação: o cliente que chega pelo link da agência fica com ela.

A agência manda para o cliente um link do site com `?ag=CODIGO`. Na primeira
página que ele abre, o código fica guardado na sessão; quando ele reservar,
a reserva sai marcada com a agência e aparece no painel dela.

Só vale código de agência aprovada. Um código errado ou de agência ainda em
análise é ignorado em silêncio: o cliente navega normalmente.
"""
from contas.models import PerfilAgente

CHAVE = 'agencia_indicacao'


class IndicacaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        codigo = request.GET.get('ag', '').strip().upper()
        if codigo and request.method == 'GET' and len(codigo) <= 12:
            agencia = PerfilAgente.objects.filter(codigo=codigo, aprovado=True).first()
            if agencia is not None:
                request.session[CHAVE] = agencia.pk
        return self.get_response(request)


def agencia_da_sessao(request):
    """A agência que indicou este visitante, se ainda estiver aprovada."""
    pk = request.session.get(CHAVE)
    if not pk:
        return None
    return PerfilAgente.objects.filter(pk=pk, aprovado=True).first()
