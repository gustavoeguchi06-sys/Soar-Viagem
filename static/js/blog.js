/* Soar Operadora — artigo do blog: o "Ler mais" das atrações abre um pop-up
   com a foto grande e o relato inteiro (templates/blog/artigo.html). */
(function () {
    'use strict';

    var popup = document.getElementById('atracaoPopup');
    if (!popup || typeof popup.showModal !== 'function') { return; }
    var foto = popup.querySelector('.atracao-popup__foto');
    var nome = popup.querySelector('#atracaoNome');
    var relato = popup.querySelector('.atracao-popup__relato');

    document.querySelectorAll('[data-atracao]').forEach(function (cartao) {
        cartao.addEventListener('click', function () {
            var img = cartao.querySelector('.blog-atracao__foto img');
            foto.innerHTML = '';
            foto.hidden = !img;
            if (img) {
                var grande = document.createElement('img');
                grande.src = img.src;
                grande.alt = '';
                foto.appendChild(grande);
            }
            nome.textContent = cartao.querySelector('b').textContent;
            // o relato já vem do servidor escapado e em parágrafos (|linebreaks)
            relato.innerHTML = cartao.querySelector('.blog-atracao__relato').innerHTML;
            popup.showModal();
        });
    });
    popup.querySelector('[data-atracao-fechar]').addEventListener('click', function () { popup.close(); });
    // clicar fora do quadro (no fundo escuro) fecha
    popup.addEventListener('click', function (ev) { if (ev.target === popup) { popup.close(); } });
})();
