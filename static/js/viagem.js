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

    // No celular as setas somem: deslizar o dedo na foto troca de foto.
    var hero = document.querySelector('.hero');
    var inicioX = null;
    if (hero) {
        hero.addEventListener('touchstart', function (e) {
            inicioX = e.touches.length === 1 ? e.touches[0].clientX : null;
        }, { passive: true });
        hero.addEventListener('touchend', function (e) {
            if (inicioX === null) { return; }
            var dx = e.changedTouches[0].clientX - inicioX;
            inicioX = null;
            if (Math.abs(dx) > 50 && !e.target.closest('.hero__thumbs')) {
                mostrarFoto(atual + (dx < 0 ? 1 : -1));
            }
        }, { passive: true });
    }

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

    /* avaliação maior que 4 linhas: mostra o "Ler tudo" */
    document.querySelectorAll('.depo').forEach(function (depo) {
        var texto = depo.querySelector('.depo__texto');
        var mais = depo.querySelector('.depo__mais');
        if (!texto || !mais || texto.scrollHeight <= texto.clientHeight + 2) { return; }
        mais.hidden = false;
        mais.addEventListener('click', function () {
            var aberto = depo.classList.toggle('aberto');
            mais.textContent = aberto ? 'Mostrar menos' : 'Ler tudo';
            mais.setAttribute('aria-expanded', aberto ? 'true' : 'false');
        });
    });
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

    /* ---------- Quartos de cada tipo na data escolhida ---------- */
    // Cada data traz em data-quartos o que o dono cadastrou ("casal:4,triplo:0").
    // O tipo sem número cadastrado na data não mostra nada; com 0, fica
    // esgotado e não dá para marcar.
    var datas = document.querySelectorAll('input[name="saida"]');
    var acoms = document.querySelectorAll('.acom');

    function mostrarQuartos() {
        var marcada = document.querySelector('input[name="saida"]:checked');
        var quartos = {};
        if (marcada && marcada.dataset.quartos) {
            marcada.dataset.quartos.split(',').forEach(function (par) {
                var p = par.split(':');
                quartos[p[0]] = parseInt(p[1], 10);
            });
        }
        acoms.forEach(function (acom) {
            var radio = acom.querySelector('input');
            var texto = acom.querySelector('[data-vagas-quarto]');
            var n = quartos[acom.dataset.tipo || radio.value];
            var esgotado = n === 0;
            acom.classList.toggle('acom--esgotada', esgotado);
            if (acom.dataset.tipo) {
                limitarQuartos(acom, n);
            } else {
                radio.disabled = esgotado;
                if (esgotado && radio.checked) { radio.checked = false; }
            }
            if (!texto) { return; }
            texto.hidden = n === undefined;
            texto.textContent = n === undefined ? '' : esgotado ? 'Esgotado nesta data'
                : n === 1 ? 'Último quarto nesta data' : n + ' quartos nesta data';
        });
    }

    /* ---------- Orçamento: quartos e pessoas de cada tipo ---------- */
    // Cada quarto leva de 1 pessoa até a lotação dele (Duplo 2, Triplo 3). Ao
    // pôr mais um quarto, as pessoas sobem junto, já lotando o quarto novo; dá
    // para baixar depois. O servidor confere tudo de novo (agencia/forms.py).
    var MAX_ADULTOS = 60;
    var caixaQuartos = document.querySelector('[data-quartos-orcamento]');

    function campoDe(acom, papel) {
        return acom.querySelector('[data-contador="' + papel + '"] input');
    }

    function numero(campo) {
        var n = parseInt(campo && campo.value, 10);
        return isNaN(n) ? 0 : n;
    }

    // o limite de quartos da data marcada (undefined = sem limite; 0 = esgotado)
    function limitarQuartos(acom, n) {
        var q = campoDe(acom, 'quartos');
        if (!q) { return; }
        var max = n === undefined ? MAX_ADULTOS : n;
        q.max = max;
        q.disabled = max === 0;
        if (numero(q) > max) { q.value = max; }
        ajustarPessoas(acom, null);
    }

    // mantém as pessoas entre 1 por quarto e a lotação; `antes` = quartos antes do clique
    function ajustarPessoas(acom, antes) {
        var q = campoDe(acom, 'quartos');
        var p = campoDe(acom, 'pessoas');
        var lotacao = parseInt(acom.dataset.lotacao, 10) || 1;
        if (!q) {   // bate-volta: sem quarto, de 0 até o máximo de pessoas
            if (p) { p.value = Math.max(0, Math.min(numero(p), MAX_ADULTOS)); }
            atualizarTotal();
            return;
        }
        var quartos = numero(q);
        if (!p) { atualizarTotal(); return; }
        var pessoas = numero(p);
        if (antes !== null && quartos > antes) { pessoas += (quartos - antes) * lotacao; }
        pessoas = Math.max(quartos, Math.min(pessoas, quartos * lotacao));
        p.value = pessoas;
        p.min = quartos;
        p.max = quartos * lotacao;
        p.disabled = quartos === 0;
        atualizarTotal();
    }

    function atualizarTotal() {
        var saida = caixaQuartos && caixaQuartos.querySelector('[data-total-quartos]');
        if (!saida) { return; }
        var adultos = 0, valor = 0, consulta = false;
        caixaQuartos.querySelectorAll('.acom--quartos').forEach(function (acom) {
            var campoQuartos = campoDe(acom, 'quartos');
            var quartos = campoQuartos ? numero(campoQuartos) : numero(campoDe(acom, 'pessoas'));
            if (!quartos) { return; }
            var pessoas = campoDe(acom, 'pessoas') ? numero(campoDe(acom, 'pessoas')) : quartos;
            adultos += pessoas;
            if (acom.dataset.preco) { valor += parseFloat(acom.dataset.preco) * pessoas; }
            else { consulta = true; }
        });
        saida.hidden = adultos === 0;
        var texto = adultos + (adultos === 1 ? ' adulto' : ' adultos');
        saida.innerHTML = '';
        var rotulo = document.createElement('span');
        rotulo.textContent = 'Total (' + texto + ')';
        var total = document.createElement('b');
        total.textContent = consulta ? 'Sob consulta'
            : valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        saida.appendChild(rotulo);
        saida.appendChild(total);
    }

    if (caixaQuartos) {
        caixaQuartos.querySelectorAll('.acom--quartos').forEach(function (acom) {
            acom.querySelectorAll('.contador__botao').forEach(function (botao) {
                botao.addEventListener('click', function () {
                    var campo = botao.parentNode.querySelector('input');
                    if (campo.disabled) { return; }
                    var antes = numero(campoDe(acom, 'quartos'));
                    var novo = numero(campo) + parseInt(botao.dataset.passo, 10);
                    var min = parseInt(campo.min, 10) || 0;
                    var max = campo.max === '' ? MAX_ADULTOS : parseInt(campo.max, 10);
                    campo.value = Math.max(min, Math.min(novo, max));
                    ajustarPessoas(acom, campo === campoDe(acom, 'quartos') ? antes : null);
                });
            });
            // digitado à mão: confere quando sai do campo
            var q = campoDe(acom, 'quartos');
            if (q) {
                var guardado = numero(q);
                q.addEventListener('focus', function () { guardado = numero(q); });
                q.addEventListener('change', function () { ajustarPessoas(acom, guardado); guardado = numero(q); });
            }
            var p = campoDe(acom, 'pessoas');
            if (p) { p.addEventListener('change', function () { ajustarPessoas(acom, null); }); }
            ajustarPessoas(acom, null);
        });
    }

    if (datas.length && acoms.length) {
        datas.forEach(function (d) { d.addEventListener('change', mostrarQuartos); });
        mostrarQuartos();
    }

    /* ---------- Álbum: as fotos abrem num carrossel ---------- */
    // Antes cada foto abria numa aba nova. Agora abre por cima da página, com
    // setas, contador e legenda; teclado (setas e Esc) e arrastar o dedo no
    // celular também passam as fotos.
    var album = document.getElementById('album');
    var fotosAlbum = Array.prototype.slice.call(document.querySelectorAll('[data-album]'));
    if (album && fotosAlbum.length && typeof album.showModal === 'function') {
        var fotoAlbum = album.querySelector('.album__foto');
        var legendaAlbum = album.querySelector('.album__legenda');
        var contadorAlbum = album.querySelector('.album__contador');
        var atualAlbum = 0;
        var sozinha = fotosAlbum.length < 2;
        album.querySelectorAll('[data-album-passo]').forEach(function (b) { b.hidden = sozinha; });

        var mostrar = function (i) {
            atualAlbum = (i + fotosAlbum.length) % fotosAlbum.length;
            var link = fotosAlbum[atualAlbum];
            fotoAlbum.src = link.getAttribute('href');
            fotoAlbum.alt = link.dataset.legenda || '';
            legendaAlbum.textContent = link.dataset.legenda || '';
            contadorAlbum.textContent = sozinha ? '' : (atualAlbum + 1) + ' de ' + fotosAlbum.length;
        };
        fotosAlbum.forEach(function (link, i) {
            link.addEventListener('click', function (ev) {
                ev.preventDefault();
                mostrar(i);
                album.showModal();
            });
        });
        album.querySelectorAll('[data-album-passo]').forEach(function (b) {
            b.addEventListener('click', function () { mostrar(atualAlbum + parseInt(b.dataset.albumPasso, 10)); });
        });
        album.querySelector('[data-album-fechar]').addEventListener('click', function () { album.close(); });
        // clicar fora da foto (no fundo escuro) fecha
        album.addEventListener('click', function (ev) { if (ev.target === album) { album.close(); } });
        album.addEventListener('keydown', function (ev) {
            if (ev.key === 'ArrowRight') { mostrar(atualAlbum + 1); }
            if (ev.key === 'ArrowLeft') { mostrar(atualAlbum - 1); }
        });
        var inicioToque = null;
        album.addEventListener('touchstart', function (ev) { inicioToque = ev.touches[0].clientX; }, { passive: true });
        album.addEventListener('touchend', function (ev) {
            if (inicioToque === null) { return; }
            var distancia = ev.changedTouches[0].clientX - inicioToque;
            if (Math.abs(distancia) > 40) { mostrar(atualAlbum + (distancia < 0 ? 1 : -1)); }
            inicioToque = null;
        });
    }

    /* ---------- Pop-ups do orçamento da agência ---------- */
    // Os <dialog> vêm com `open` para funcionar sem JavaScript (aparecem no
    // lugar). Aqui eles fecham e passam a abrir como pop-up de verdade: o do
    // "Criar orçamento" no clique, e o que tem data-abrir-ja (aviso depois de
    // criar, ou campo com erro) assim que a página carrega.
    var popups = document.querySelectorAll('dialog[data-popup]');
    popups.forEach(function (popup) {
        if (typeof popup.showModal !== 'function') { return; }
        popup.close();
        popup.classList.add('popup--modal');
        if (popup.hasAttribute('data-abrir-ja')) { popup.showModal(); }
        // clicar no fundo escuro fecha
        popup.addEventListener('click', function (ev) {
            if (ev.target === popup) { popup.close(); }
        });
    });
    // O aviso do "Saiba mais" vem de ?enviado=1: tira do endereço depois de
    // mostrar, para não abrir de novo quando a pessoa recarrega a página
    if (/[?&](enviado|avaliacao)=1/.test(location.search) && window.history.replaceState) {
        var endereco = new URL(location.href);
        endereco.searchParams.delete('enviado');
        endereco.searchParams.delete('avaliacao');
        history.replaceState(null, '', endereco);
    }
    document.querySelectorAll('[data-abrir-popup]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            var popup = document.getElementById(botao.dataset.abrirPopup);
            if (popup && typeof popup.showModal === 'function') { popup.showModal(); }
        });
    });
    document.querySelectorAll('[data-fechar-popup]').forEach(function (botao) {
        botao.addEventListener('click', function () { botao.closest('dialog').close(); });
    });
}());
