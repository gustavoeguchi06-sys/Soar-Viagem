"""Desliga o service worker que outro sistema deixou no navegador.

O site da Soar não usa service worker. Mas quem roda mais de um projeto
Django na mesma máquina abre todos em http://127.0.0.1:8000, e o navegador
guarda o service worker por endereço, não por projeto. Um app com
notificação (ou modo offline) que já rodou nesse endereço deixa o dele
registrado, e ele continua interceptando as páginas da Soar: umas carregam,
outras dão erro e só abrem na segunda tentativa. O rastro disso no
rodar.log é um "GET /sw.js 404" a cada página aberta, porque o navegador
tenta atualizar o worker e não acha o arquivo.

A saída é responder em /sw.js com um worker que se desinstala: o navegador
vê que o arquivo mudou, instala este no lugar do antigo, e este apaga os
caches, cancela o próprio registro e recarrega as abas abertas. Depois disso
nenhum service worker fica controlando o site.
"""
from django.http import HttpResponse
from django.shortcuts import redirect
from django.templatetags.static import static

SCRIPT = """// Soar: remove o service worker antigo deste endereço.
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (evento) {
    evento.waitUntil((async function () {
        var nomes = await caches.keys();
        await Promise.all(nomes.map(function (nome) { return caches.delete(nome); }));
        await self.registration.unregister();
        var abas = await self.clients.matchAll({ type: 'window' });
        abas.forEach(function (aba) { aba.navigate(aba.url); });
    })());
});
"""


def service_worker(request):
    resposta = HttpResponse(SCRIPT, content_type='application/javascript; charset=utf-8')
    resposta['Cache-Control'] = 'no-store'
    return resposta


def favicon(request):
    """O ícone da aba: a logo da Soar."""
    return redirect(static('img/logo-soar.png'), permanent=True)
