// Tela "Site em andamento!" (templates/partials/_em_andamento.html): o resto da
// página fica fora do alcance do teclado e do leitor de tela, e o foco vai
// para o botão das reservas.
(function () {
    var tela = document.querySelector('.em-andamento');
    if (!tela) { return; }
    Array.prototype.forEach.call(document.body.children, function (el) {
        if (el !== tela && !el.contains(tela)) { el.inert = true; }
    });
    var botao = tela.querySelector('a');
    if (botao) { botao.focus(); }
})();
