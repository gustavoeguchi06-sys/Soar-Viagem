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
    var barraAbas = document.querySelector('.abas');
    var tirinhaAbas = document.querySelector('.abas__inner');

    /* em telas estreitas a faixa de abas não cabe inteira: marca a borda com um
       degradê e mantém a aba ativa visível conforme a página rola */
    function marcarRolagem() {
        if (!tirinhaAbas) { return; }
        var sobra = tirinhaAbas.scrollWidth - tirinhaAbas.clientWidth;
        barraAbas.classList.toggle('rola', sobra > 4 && tirinhaAbas.scrollLeft < sobra - 4);
    }

    function trazerParaVista(aba) {
        if (!tirinhaAbas || tirinhaAbas.scrollWidth <= tirinhaAbas.clientWidth) { return; }
        var a = aba.getBoundingClientRect();
        var t = tirinhaAbas.getBoundingClientRect();
        if (a.left < t.left + 8 || a.right > t.right - 8) {
            tirinhaAbas.scrollLeft += a.left - t.left - (t.width - a.width) / 2;
        }
    }

    if (tirinhaAbas) {
        tirinhaAbas.addEventListener('scroll', marcarRolagem, { passive: true });
        window.addEventListener('resize', marcarRolagem, { passive: true });
        marcarRolagem();
    }

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

    var abaAtiva = -1;

    function marcarAba() {
        var y = window.pageYOffset + 140;
        var ativa = 0;
        alvos.forEach(function (alvo, i) {
            if (alvo && alvo.offsetTop <= y) { ativa = i; }
        });
        abas.forEach(function (a, i) { a.classList.toggle('ativa', i === ativa); });
        if (ativa !== abaAtiva) {
            abaAtiva = ativa;
            if (abas[ativa]) { trazerParaVista(abas[ativa]); }
        }
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
