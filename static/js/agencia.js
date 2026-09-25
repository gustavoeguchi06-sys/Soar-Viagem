// Painel da agência: botões de copiar e mostrar só as datas de
// saída do destino escolhido no orçamento.
(function () {
    document.querySelectorAll('[data-copiar]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            var campo = document.getElementById(botao.dataset.copiar);
            if (!campo) return;
            var texto = botao.textContent;
            var pronto = function () {
                botao.textContent = 'Copiado!';
                setTimeout(function () { botao.textContent = texto; }, 1800);
            };
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(campo.value).then(pronto);
            } else {
                campo.select();
                document.execCommand('copy');
                pronto();
            }
        });
    });

    var destino = document.getElementById('id_destino');
    var saida = document.getElementById('id_saida_escolhida');
    if (!destino || !saida) return;

    function filtrar() {
        var nome = destino.selectedIndex > 0 ? destino.options[destino.selectedIndex].text : '';
        var grupos = saida.querySelectorAll('optgroup');
        grupos.forEach(function (grupo) {
            var mostra = !nome || grupo.label === nome;
            grupo.hidden = !mostra;
            grupo.disabled = !mostra;
        });
        var escolhida = saida.options[saida.selectedIndex];
        if (escolhida && escolhida.parentNode.disabled) saida.value = '';
    }
    destino.addEventListener('change', filtrar);
    filtrar();
})();
