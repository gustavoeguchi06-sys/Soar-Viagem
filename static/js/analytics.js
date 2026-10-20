/* Google Analytics 4 com consentimento (LGPD).

   O base.html só inclui este arquivo quando o SOAR_GA_ID está configurado, e
   passa o ID no atributo data-ga da própria tag <script>. Nada do Google é
   baixado antes do visitante clicar em "Aceitar" no banner de cookies.

   A escolha fica no localStorage ("soar-cookies"), com a data: depois de 12
   meses o banner pergunta de novo. "Preferências de cookies", no rodapé e no
   aviso de privacidade, reabre o banner. Quem recusa depois de ter aceitado
   tem os cookies _ga apagados. */
(function () {
    'use strict';

    var tag = document.currentScript;
    var ID = tag && tag.getAttribute('data-ga');
    if (!ID) return;

    var CHAVE = 'soar-cookies';
    var VALIDADE = 365 * 24 * 3600 * 1000;
    var carregado = false;

    function lerEscolha() {
        try {
            var salvo = JSON.parse(localStorage.getItem(CHAVE) || 'null');
            if (salvo && (salvo.v === 'aceito' || salvo.v === 'recusado')
                    && Date.now() - salvo.em < VALIDADE) {
                return salvo.v;
            }
        } catch (e) { /* navegação privada ou valor estragado */ }
        return null;
    }

    function guardar(valor) {
        try { localStorage.setItem(CHAVE, JSON.stringify({ v: valor, em: Date.now() })); }
        catch (e) { /* sem armazenamento: vale só para esta página */ }
    }

    function carregarGA() {
        if (carregado) return;
        carregado = true;
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        // só estatística: nada de anúncio nem de personalização
        window.gtag('consent', 'default', {
            analytics_storage: 'granted',
            ad_storage: 'denied',
            ad_user_data: 'denied',
            ad_personalization: 'denied'
        });
        window.gtag('js', new Date());
        window.gtag('config', ID);
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ID);
        document.head.appendChild(s);
    }

    function apagarCookiesGA() {
        var partes = location.hostname.split('.');
        var dominios = [''];
        for (var i = 0; i < partes.length - 1; i++) {
            dominios.push('; domain=.' + partes.slice(i).join('.'));
        }
        document.cookie.split(';').forEach(function (c) {
            var nome = c.split('=')[0].trim();
            if (nome === '_ga' || nome.indexOf('_ga_') === 0 || nome === '_gid') {
                dominios.forEach(function (d) {
                    document.cookie = nome + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
                });
            }
        });
    }

    function iniciar() {
        var banner = document.getElementById('banner-cookies');
        var escolha = lerEscolha();

        function mostrar() {
            if (!banner) return;
            banner.hidden = false;
            var aceitar = banner.querySelector('[data-cookies="aceitar"]');
            if (aceitar) aceitar.focus({ preventScroll: true });
        }

        function decidir(valor) {
            var antes = lerEscolha();
            guardar(valor);
            if (banner) banner.hidden = true;
            if (valor === 'aceito') {
                carregarGA();
            } else if (antes === 'aceito' || carregado) {
                apagarCookiesGA();
                // o gtag já carregado continuaria rodando nesta página
                if (carregado) location.reload();
            }
        }

        if (escolha === 'aceito') carregarGA();
        else if (escolha === null) mostrar();

        if (banner) {
            banner.addEventListener('click', function (e) {
                var botao = e.target.closest('[data-cookies]');
                if (!botao) return;
                decidir(botao.getAttribute('data-cookies') === 'aceitar' ? 'aceito' : 'recusado');
            });
        }
        document.addEventListener('click', function (e) {
            if (e.target.closest('[data-cookies-preferencias]')) {
                e.preventDefault();
                mostrar();
            }
        });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
    else iniciar();
})();
