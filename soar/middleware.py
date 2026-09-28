"""Content-Security-Policy.

O Django só ganhou CSP nativo na versão 6.0; aqui ainda é a 5.2, então o
cabeçalho é montado à mão. São poucas linhas e não traz dependência nova.

A política vale de verdade por padrão. Com SOAR_CSP_SOMENTE_RELATORIO=1 ela
sai como `Content-Security-Policy-Report-Only`: o navegador só reclama no
console, sem bloquear — útil para investigar algo que parou de funcionar.
"""
import logging

from django.conf import settings
from django.shortcuts import render


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


class LimiteDeEnvioMiddleware:
    """Recusa, antes de ler, um envio maior do que o site aceita.

    O limite de 2 MB da foto de avaliação só era conferido pelo formulário,
    depois que o arquivo inteiro já tinha subido e ido para o disco: alguém
    logado podia mandar um arquivo de vários GB e encher o servidor. E as
    fotos do painel não tinham limite nenhum.

    O Django só lê o corpo da requisição quando alguém pede `request.POST` ou
    `request.FILES`. Olhando o Content-Length aqui, no começo da fila, o envio
    grande é recusado sem que um byte dele seja lido. Em produção o Nginx faz
    o mesmo com `client_max_body_size` (ver README), e os dois valores devem
    ser iguais.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            tamanho = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            tamanho = 0
        limite = settings.TAMANHO_MAXIMO_ENVIO
        if tamanho > limite:
            logging.getLogger('soar.seguranca').warning(
                'envio recusado por tamanho: %d bytes (limite %d) caminho=%s',
                tamanho, limite, request.path)
            return render(request, '413.html', {'limite_mb': limite // (1024 * 1024)},
                          status=413)
        return self.get_response(request)
