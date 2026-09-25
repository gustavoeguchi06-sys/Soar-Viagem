/* Soar Operadora — cabeçalho (vale para todas as páginas)
   Abre e fecha o menu das telas pequenas, que substitui o `.topnav`
   escondido abaixo de 1080px. */
(function () {
    'use strict';

    /* ---------- Avisos: somem sozinhos depois de 4 segundos ---------- */
    var TEMPO_NA_TELA = 4000;   /* quanto o aviso fica visivel */
    var TEMPO_MINIMO = 1200;    /* mesmo chegando atrasado, da tempo de ler */
    var TEMPO_DA_SAIDA = 350;   /* tem que bater com o transition do .aviso */

    var caixaDeAvisos = document.querySelector('.avisos');
    if (caixaDeAvisos) {
        var avisos = caixaDeAvisos.querySelectorAll('.aviso');
        var restantes = avisos.length;

        /* O script roda com defer: ele so comeca depois do HTML todo, quando o
           aviso ja esta na tela ha um tempinho. Por isso o prazo conta desde o
           carregamento da pagina, e nao daqui. O piso existe para o caso de o
           script chegar muito atrasado — sem ele, o aviso sumiria na hora e a
           pessoa nao leria nada. */
        var jaPassou = performance.now();
        var esperar = Math.max(TEMPO_MINIMO, TEMPO_NA_TELA - jaPassou);

        avisos.forEach(function (aviso) {
            setTimeout(function () {
                aviso.classList.add('aviso--saindo');
                /* nao espera o transitionend: quem desligou animacao no sistema
                   nao dispara o evento, e o aviso ficaria preso na tela */
                setTimeout(function () {
                    aviso.remove();
                    restantes -= 1;
                    if (restantes <= 0) { caixaDeAvisos.remove(); }
                }, TEMPO_DA_SAIDA);
            }, esperar);
        });
    }

    /* O menu da conta e um <details>: abre e fecha sozinho. So falta fechar
       quando a pessoa clica em qualquer outro lugar da pagina. */
    var conta = document.querySelector('.conta');
    if (conta) {
        document.addEventListener('click', function (evento) {
            if (conta.open && !evento.target.closest('.conta')) { conta.open = false; }
        });
        document.addEventListener('keydown', function (evento) {
            if (evento.key === 'Escape' && conta.open) { conta.open = false; }
        });
    }

    /* Formulário que pede confirmação antes de enviar (ex.: cancelar reserva).
       Fica aqui, e não num onsubmit="" no HTML, porque a política de
       segurança do site (CSP) bloqueia JavaScript escrito dentro do HTML. */
    document.querySelectorAll('form[data-confirmar]').forEach(function (form) {
        form.addEventListener('submit', function (evento) {
            if (!window.confirm(form.dataset.confirmar)) { evento.preventDefault(); }
        });
    });

    /* Botão de tema: troca claro/escuro e guarda a escolha no navegador. */
    var botaoTema = document.getElementById('botaoTema');
    function rotularTema() {
        var escuro = document.documentElement.getAttribute('data-tema') === 'escuro';
        botaoTema.setAttribute('aria-label', escuro ? 'Mudar para o tema claro' : 'Mudar para o tema escuro');
        botaoTema.setAttribute('title', escuro ? 'Tema claro' : 'Tema escuro');
    }
    if (botaoTema) {
        rotularTema();
        botaoTema.addEventListener('click', function () {
            var escuro = document.documentElement.getAttribute('data-tema') !== 'escuro';
            document.documentElement.setAttribute('data-tema', escuro ? 'escuro' : 'claro');
            try { localStorage.setItem('theme', escuro ? 'dark' : 'light'); } catch (e) { /* sem armazenamento */ }
            rotularTema();
        });
    }

    var botao = document.getElementById('menuBotao');
    var menu = document.getElementById('menuMovel');
    if (!botao || !menu) { return; }

    function fechar() {
        menu.hidden = true;
        botao.setAttribute('aria-expanded', 'false');
        botao.setAttribute('aria-label', 'Abrir menu');
        document.body.classList.remove('menu-aberto');
    }

    function abrir() {
        menu.hidden = false;
        botao.setAttribute('aria-expanded', 'true');
        botao.setAttribute('aria-label', 'Fechar menu');
        document.body.classList.add('menu-aberto');
    }

    botao.addEventListener('click', function () {
        if (menu.hidden) { abrir(); } else { fechar(); }
    });

    menu.addEventListener('click', function (evento) {
        if (evento.target.closest('a')) { fechar(); }
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape' && !menu.hidden) { fechar(); botao.focus(); }
    });

    document.addEventListener('click', function (evento) {
        if (!menu.hidden && !evento.target.closest('.topbar')) { fechar(); }
    });

    // ao voltar para a largura em que o .topnav reaparece, o menu não faz sentido
    var largo = window.matchMedia('(min-width: 1081px)');
    var aoMudar = function (consulta) { if (consulta.matches) { fechar(); } };
    if (largo.addEventListener) { largo.addEventListener('change', aoMudar); }
    else if (largo.addListener) { largo.addListener(aoMudar); }
}());
