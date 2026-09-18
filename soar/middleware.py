"""Content-Security-Policy.

O Django só ganhou CSP nativo na versão 6.0; aqui ainda é a 5.2, então o
cabeçalho é montado à mão. São poucas linhas e não traz dependência nova.

A política sai em modo de relatório por padrão (`Content-Security-Policy-
Report-Only`): o navegador reclama no console mas não bloqueia nada. Rode
assim por alguns dias, veja o que aparece e só então mude
SOAR_CSP_SOMENTE_RELATORIO=0 para passar a valer de verdade.
"""
from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Acrescenta a CSP a toda resposta HTML."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.politica = '; '.join(
            '{} {}'.format(nome, valor)
            for nome, valor in settings.CSP_DIRETIVAS.items()
        )

    def __call__(self, request):
        resposta = self.get_response(request)

        cabecalho = ('Content-Security-Policy-Report-Only'
                     if settings.CSP_SOMENTE_RELATORIO else 'Content-Security-Policy')

        # Não sobrescreve uma política que a própria view tenha definido, e não
        # gasta o cabeçalho em imagem ou download, onde ele não faz diferença.
        ja_tem = ('Content-Security-Policy' in resposta
                  or 'Content-Security-Policy-Report-Only' in resposta)
        if not ja_tem and self._e_html(resposta):
            resposta[cabecalho] = self.politica

        # Desliga recursos do navegador que o site não usa. Se um XSS um dia
        # passar, ele já não pede câmera, microfone nem localização.
        resposta.setdefault('Permissions-Policy',
                            'camera=(), microphone=(), geolocation=(), interest-cohort=()')
        return resposta

    @staticmethod
    def _e_html(resposta):
        return resposta.get('Content-Type', '').startswith('text/html')
