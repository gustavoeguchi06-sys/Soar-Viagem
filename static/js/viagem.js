/* Soar Operadora — interações da página de viagem
   ---------------------------------------------------------------------------
   1. galeria do hero
   2. abas do miolo
   3. calendário de embarque
   4. pacote, duração, opcionais e total (card lateral)
--------------------------------------------------------------------------- */
(function () {
    'use strict';

    var MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
    var SEMANA = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
                  'Quinta-feira', 'Sexta-feira', 'Sábado'];

    var fonte = document.getElementById('dados-viagem');
    var dados = fonte ? JSON.parse(fonte.textContent) : null;

    function pegar(id) { return document.getElementById(id); }

    function moeda(valor) {
        return 'R$ ' + Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 0 });
    }

    function doisDigitos(n) { return (n < 10 ? '0' : '') + n; }

    /* ===================== 1. galeria do hero ===================== */
    (function galeriaHero() {
        var foto = pegar('heroFoto');
        var botoes = Array.prototype.slice.call(document.querySelectorAll('.hero__thumbs button'));
        if (!foto || !botoes.length) { return; }

        botoes.forEach(function (botao) {
            botao.addEventListener('click', function () {
                foto.src = botao.dataset.foto;
                botoes.forEach(function (b) { b.classList.remove('ativo'); });
                if (!botao.classList.contains('mais')) { botao.classList.add('ativo'); }
            });
        });
    }());

    /* ===================== 2. abas do miolo ===================== */
    (function abas() {
        var botoes = Array.prototype.slice.call(document.querySelectorAll('.aba'));
        var paineis = Array.prototype.slice.call(document.querySelectorAll('.painel-aba'));
        if (!botoes.length) { return; }

        function abrir(chave, rolar) {
            botoes.forEach(function (b) { b.classList.toggle('ativa', b.dataset.aba === chave); });
            paineis.forEach(function (p) { p.classList.toggle('ativo', p.dataset.painel === chave); });
            if (rolar) {
                var barra = document.querySelector('.abas');
                var topo = barra.getBoundingClientRect().top + window.pageYOffset;
                if (window.pageYOffset > topo) { window.scrollTo({ top: topo, behavior: 'smooth' }); }
            }
        }

        botoes.forEach(function (botao) {
            botao.addEventListener('click', function () { abrir(botao.dataset.aba, true); });
        });
        document.querySelectorAll('[data-ir-aba]').forEach(function (atalho) {
            atalho.addEventListener('click', function () { abrir(atalho.dataset.irAba, true); });
        });

        // quando o formulário de avaliação volta com erro, já abre a aba certa
        function abrirPeloEndereco() {
            var chave = window.location.hash.replace('#', '');
            if (paineis.some(function (p) { return p.dataset.painel === chave; })) {
                abrir(chave, false);
            }
        }
        if (document.querySelector('.campo-erro')) { abrir('avaliacoes', false); }
        abrirPeloEndereco();
        window.addEventListener('hashchange', abrirPeloEndereco);
    }());

    if (!dados) { return; }

    /* ===================== 3. calendário ===================== */
    var hoje = new Date();
    hoje.setHours(0, 0, 0, 0);

    var selecionada = new Date(dados.ano, dados.mes - 1, dados.dia);
    if (selecionada < hoje) { selecionada = new Date(hoje); }

    var visivel = new Date(selecionada.getFullYear(), selecionada.getMonth(), 1);
    var confirmada = false;   // vira true quando a pessoa escolhe uma data no calendário

    var calMes = pegar('calMes');
    var calDias = pegar('calDias');

    function mesmaData(a, b) {
        return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
            && a.getDate() === b.getDate();
    }

    function desenharCalendario() {
        if (!calDias) { return; }
        calMes.textContent = MESES[visivel.getMonth()] + ' ' + visivel.getFullYear();

        var primeiro = new Date(visivel.getFullYear(), visivel.getMonth(), 1);
        var inicio = new Date(primeiro);
        inicio.setDate(1 - primeiro.getDay());   // recua até o domingo da primeira semana

        calDias.innerHTML = '';
        for (var i = 0; i < 42; i += 1) {
            var data = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i);
            var botao = document.createElement('button');
            botao.type = 'button';
            botao.className = 'cal__dia';
            botao.textContent = data.getDate();

            var deOutroMes = data.getMonth() !== visivel.getMonth();
            var passado = data < hoje;

            if (deOutroMes || passado) {
                botao.classList.add('fora');
                botao.disabled = true;
            } else {
                botao.dataset.data = data.toISOString().slice(0, 10);
            }
            if (mesmaData(data, selecionada)) { botao.classList.add('ativo'); }

            calDias.appendChild(botao);
        }

        var anterior = document.querySelector('.cal__nav[data-mes="-1"]');
        if (anterior) {
            anterior.disabled = visivel.getFullYear() === hoje.getFullYear()
                && visivel.getMonth() === hoje.getMonth();
        }
    }

    function textoData(data) {
        return doisDigitos(data.getDate()) + '/' + doisDigitos(data.getMonth() + 1) + '/'
            + data.getFullYear();
    }

    function mostrarData() {
        var texto = textoData(selecionada);
        var semana = SEMANA[selecionada.getDay()];

        if (pegar('resumoData')) { pegar('resumoData').textContent = texto; }
        if (pegar('resumoSemana')) { pegar('resumoSemana').textContent = '(' + semana + ')'; }
        if (pegar('latData')) {
            pegar('latData').textContent = texto + ' (' + semana.replace('-feira', '').toLowerCase() + ')';
        }
        if (confirmada && pegar('campoData')) { pegar('campoData').value = texto; }
    }

    if (calDias) {
        calDias.addEventListener('click', function (evento) {
            var botao = evento.target.closest('.cal__dia');
            if (!botao || !botao.dataset.data) { return; }
            var partes = botao.dataset.data.split('-');
            selecionada = new Date(+partes[0], partes[1] - 1, +partes[2]);
            confirmada = true;
            desenharCalendario();
            mostrarData();
        });
    }

    document.querySelectorAll('.cal__nav').forEach(function (botao) {
        botao.addEventListener('click', function () {
            visivel.setMonth(visivel.getMonth() + parseInt(botao.dataset.mes, 10));
            desenharCalendario();
        });
    });

    /* ===================== 4. pacote, duração, opcionais e total ============ */
    var campoDuracao = pegar('campoDuracao');

    function duracaoAtual() {
        return campoDuracao ? campoDuracao.value : dados.duracaoPadrao;
    }

    function pacoteAtual() {
        var marcado = document.querySelector('input[name="pacote"]:checked');
        var chave = marcado ? marcado.value : dados.pacotePadrao;
        return dados.pacotes.filter(function (p) { return p.chave === chave; })[0];
    }

    function precoDoPacote(pacote) {
        if (!pacote || pacote.consulte) { return null; }
        return pacote.precos[duracaoAtual()];
    }

    function totalOpcionais() {
        var soma = 0;
        document.querySelectorAll('[data-opcional]:checked').forEach(function (caixa) {
            soma += parseInt(caixa.dataset.preco, 10) || 0;
        });
        return soma;
    }

    function atualizar() {
        var duracao = duracaoAtual();

        // preço de cada cartão de pacote, na duração escolhida
        dados.pacotes.forEach(function (p) {
            var alvo = document.querySelector('[data-preco-pacote="' + p.chave + '"]');
            if (alvo && !p.consulte) { alvo.textContent = moeda(p.precos[duracao]); }
        });

        var rotulo = dados.duracoes.filter(function (d) { return d.chave === duracao; })[0];
        if (rotulo) {
            if (pegar('resumoDuracao')) { pegar('resumoDuracao').textContent = rotulo.rotulo; }
            if (pegar('latDuracao')) { pegar('latDuracao').textContent = rotulo.rotulo; }
        }

        var pacote = pacoteAtual();
        var preco = precoDoPacote(pacote);

        if (pegar('latPacote')) { pegar('latPacote').textContent = pacote.nome; }
        if (pegar('latPessoas')) { pegar('latPessoas').textContent = pacote.pessoas || ''; }
        if (pegar('latPacotePreco')) {
            pegar('latPacotePreco').textContent = preco === null ? 'Consulte' : moeda(preco);
        }
        if (pegar('latTotal')) {
            pegar('latTotal').textContent = preco === null ? 'Consulte' : moeda(preco + totalOpcionais());
        }
        if (pegar('latParcelas')) {
            pegar('latParcelas').textContent = preco === null
                ? 'fale com a nossa equipe'
                : 'em até ' + dados.parcelas + 'x sem juros';
        }
    }

    if (campoDuracao) { campoDuracao.addEventListener('change', atualizar); }
    document.querySelectorAll('input[name="pacote"]').forEach(function (radio) {
        radio.addEventListener('change', atualizar);
    });
    document.querySelectorAll('[data-opcional]').forEach(function (caixa) {
        caixa.addEventListener('change', atualizar);
    });

    // o campo de data rola até o calendário
    if (pegar('campoData') && calDias) {
        pegar('campoData').addEventListener('click', function () {
            calDias.closest('.cal').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    desenharCalendario();
    mostrarData();
    atualizar();

    /* ===================== avisos somem sozinhos ===================== */
    document.querySelectorAll('.aviso').forEach(function (aviso) {
        setTimeout(function () {
            aviso.style.transition = 'opacity .4s';
            aviso.style.opacity = '0';
            setTimeout(function () { aviso.remove(); }, 400);
        }, 4500);
    });
}());
