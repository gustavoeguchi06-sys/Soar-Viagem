/* Soar Operadora — cabeçalho (vale para todas as páginas)
   Abre e fecha o menu das telas pequenas, que substitui o `.topnav`
   escondido abaixo de 1080px. */
(function () {
    'use strict';

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
