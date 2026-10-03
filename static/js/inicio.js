/* Soar Operadora — página inicial: carrossel do topo, trilho de viagens e depoimentos. */
(function () {
    'use strict';

    var reduzir = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- Carrossel do topo ---------- */
    var hero = document.querySelector('.in-hero');
    var fotos = hero ? Array.prototype.slice.call(hero.querySelectorAll('.in-hero__foto')) : [];
    var pontos = hero ? Array.prototype.slice.call(hero.querySelectorAll('.in-hero__pontos button')) : [];
    var atual = 0, relogio = null;

    // Slide de vídeo: só o que está na tela toca. Quem pediu menos movimento
    // no aparelho vê só a capa (a foto), sem o vídeo andar.
    function tocarVideos() {
        fotos.forEach(function (f, k) {
            if (f.tagName !== 'VIDEO') { return; }
            if (k === atual && !reduzir) {
                f.preload = 'auto';
                var tentativa = f.play();
                if (tentativa && tentativa.catch) { tentativa.catch(function () {}); }
            } else {
                f.pause();
            }
        });
    }
    function mostrar(i) {
        if (fotos.length < 2) { return; }
        atual = (i + fotos.length) % fotos.length;
        fotos.forEach(function (f, k) { f.classList.toggle('ativo', k === atual); });
        pontos.forEach(function (p, k) { p.classList.toggle('ativo', k === atual); });
        tocarVideos();
    }
    tocarVideos();
    function tocar() {
        parar();
        if (!reduzir && fotos.length > 1) { relogio = setInterval(function () { mostrar(atual + 1); }, 6000); }
    }
    function parar() { if (relogio) { clearInterval(relogio); relogio = null; } }

    if (hero && fotos.length > 1) {
        hero.querySelectorAll('[data-slide]').forEach(function (b) {
            b.addEventListener('click', function () { mostrar(atual + parseInt(b.dataset.slide, 10)); tocar(); });
        });
        pontos.forEach(function (p) {
            p.addEventListener('click', function () { mostrar(parseInt(p.dataset.ir, 10)); tocar(); });
        });
        hero.addEventListener('mouseenter', parar);
        hero.addEventListener('mouseleave', tocar);
        // deslizar o dedo troca a foto
        var x0 = null;
        hero.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
        hero.addEventListener('touchend', function (e) {
            if (x0 === null) { return; }
            var dx = e.changedTouches[0].clientX - x0; x0 = null;
            if (Math.abs(dx) > 50 && !e.target.closest('a, button')) { mostrar(atual + (dx < 0 ? 1 : -1)); tocar(); }
        }, { passive: true });
        document.addEventListener('visibilitychange', function () { if (document.hidden) { parar(); } else { tocar(); } });
        tocar();
    }

    /* ---------- Trilho de próximas viagens ---------- */
    var trilho = document.querySelector('.in-trilho');
    document.querySelectorAll('[data-trilho]').forEach(function (b) {
        b.addEventListener('click', function () {
            if (!trilho) { return; }
            var card = trilho.firstElementChild;
            var passo = card ? card.getBoundingClientRect().width + 18 : 280;
            trilho.scrollBy({ left: passo * parseInt(b.dataset.trilho, 10), behavior: reduzir ? 'auto' : 'smooth' });
        });
    });

    /* ---------- Busca: o "Quando?" mostra só os meses do destino escolhido ---------- */
    var buscaDestino = document.getElementById('buscaDestino');
    var buscaMes = document.getElementById('buscaMes');
    if (buscaDestino && buscaMes) {
        var opcoesMes = Array.prototype.slice.call(buscaMes.options, 1);
        var filtrarMeses = function () {
            var destino = buscaDestino.value;
            opcoesMes.forEach(function (op) {
                var serve = !destino || op.dataset.destinos.split('|').indexOf(destino) !== -1;
                op.hidden = !serve;
                op.disabled = !serve;
                if (!serve && op.selected) { buscaMes.value = ''; }
            });
        };
        buscaDestino.addEventListener('change', filtrarMeses);
        filtrarMeses();
    }

    /* ---------- Depoimentos ---------- */
    var itens = Array.prototype.slice.call(document.querySelectorAll('.in-depo__item'));
    var depo = 0;
    document.querySelectorAll('[data-depo]').forEach(function (b) {
        b.addEventListener('click', function () {
            if (itens.length < 2) { return; }
            depo = (depo + parseInt(b.dataset.depo, 10) + itens.length) % itens.length;
            itens.forEach(function (it, k) { it.classList.toggle('ativo', k === depo); });
        });
    });
})();
