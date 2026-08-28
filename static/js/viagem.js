/* Soar Operadora — interações da página de viagem */
(function () {
    'use strict';

    /* ---------- Carrossel do hero ---------- */
    var heroFoto = document.getElementById('heroFoto');
    var thumbs = Array.prototype.slice.call(document.querySelectorAll('.hero__thumbs button'));
    var fotos = thumbs.map(function (b) { return b.dataset.foto; });
    var atual = 0;

    function mostrarFoto(i) {
        if (!heroFoto || !fotos.length) { return; }
        atual = (i + fotos.length) % fotos.length;
        heroFoto.src = fotos[atual];
        thumbs.forEach(function (b, k) { b.classList.toggle('ativo', k === atual); });
    }

    thumbs.forEach(function (botao, i) {
        botao.addEventListener('click', function () { mostrarFoto(i); });
    });
    document.querySelectorAll('[data-hero]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            mostrarFoto(atual + parseInt(botao.dataset.hero, 10));
        });
    });

    /* ---------- Carrossel da hospedagem ---------- */
    var hospFoto = document.getElementById('hospFoto');
    var hospMinis = Array.prototype.slice.call(document.querySelectorAll('.hosp-mini img'));
    var hospFotos = hospFoto ? [hospFoto.src].concat(hospMinis.map(function (i) { return i.src; })) : [];
    var hospAtual = 0;

    document.querySelectorAll('[data-hosp]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            if (!hospFotos.length) { return; }
            hospAtual = (hospAtual + parseInt(botao.dataset.hosp, 10) + hospFotos.length) % hospFotos.length;
            hospFoto.src = hospFotos[hospAtual];
        });
    });
    hospMinis.forEach(function (img) {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function () {
            var troca = hospFoto.src;
            hospFoto.src = img.src;
            img.src = troca;
        });
    });

    /* ---------- Roteiro completo ---------- */
    var verRoteiro = document.getElementById('verRoteiro');
    if (verRoteiro) {
        verRoteiro.addEventListener('click', function () {
            var dias = document.querySelectorAll('#roteiroLista .dia');
            var abrir = !Array.prototype.every.call(dias, function (d) { return d.open; });
            dias.forEach(function (d) { d.open = abrir; });
            verRoteiro.textContent = abrir ? 'Recolher roteiro' : 'Ver roteiro completo';
        });
    }

    /* ---------- Carrossel de depoimentos ---------- */
    var trilho = document.getElementById('trilhoDepo');
    document.querySelectorAll('[data-depo]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            if (!trilho) { return; }
            var card = trilho.querySelector('.depo');
            var passo = card ? card.offsetWidth + 14 : 260;
            trilho.scrollBy({ left: passo * parseInt(botao.dataset.depo, 10), behavior: 'smooth' });
        });
    });

    /* ---------- Abas: rolagem suave + aba ativa ---------- */
    var abas = Array.prototype.slice.call(document.querySelectorAll('.abas a'));
    var alvos = abas.map(function (a) { return document.querySelector(a.getAttribute('href')); });

    abas.forEach(function (aba, i) {
        aba.addEventListener('click', function (evento) {
            var alvo = alvos[i];
            if (!alvo) { return; }
            evento.preventDefault();
            var topo = alvo.getBoundingClientRect().top + window.pageYOffset - 76;
            window.scrollTo({ top: topo, behavior: 'smooth' });
            if (alvo.tagName === 'DETAILS') { alvo.open = true; }
        });
    });

    function marcarAba() {
        var y = window.pageYOffset + 140;
        var ativa = 0;
        alvos.forEach(function (alvo, i) {
            if (alvo && alvo.offsetTop <= y) { ativa = i; }
        });
        abas.forEach(function (a, i) { a.classList.toggle('ativa', i === ativa); });
    }

    window.addEventListener('scroll', marcarAba, { passive: true });
    marcarAba();

    /* ---------- Avisos somem sozinhos ---------- */
    document.querySelectorAll('.aviso').forEach(function (aviso) {
        setTimeout(function () {
            aviso.style.transition = 'opacity .4s';
            aviso.style.opacity = '0';
            setTimeout(function () { aviso.remove(); }, 400);
        }, 4500);
    });
}());
