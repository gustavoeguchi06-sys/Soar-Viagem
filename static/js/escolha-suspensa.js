/* Campo "abre e fecha" com caixinhas (blog/admin.py, EscolhaSuspensa).
   O <details> já abre e fecha sozinho; aqui só:
   - o resumo do botão acompanha o que está marcado;
   - a busca esconde as viagens que não batem com o texto;
   - Enter na busca não envia o formulário;
   - clicar fora ou apertar Esc fecha. */
(function () {
    'use strict';

    function semAcento(t) {
        return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }

    function preparar(caixa) {
        var resumo = caixa.querySelector('.escolha-suspensa__resumo');
        var busca = caixa.querySelector('.escolha-suspensa__busca');
        var nada = caixa.querySelector('.escolha-suspensa__nada');
        var itens = Array.prototype.slice.call(caixa.querySelectorAll('.escolha-suspensa__lista label'));
        var vazio = caixa.getAttribute('data-vazio');

        function atualizarResumo() {
            var nomes = itens.filter(function (l) {
                var c = l.querySelector('input');
                return c && c.checked;
            }).map(function (l) { return l.textContent.trim().replace(/, Brasil$/, ''); });
            if (!nomes.length) resumo.textContent = vazio;
            else if (nomes.length <= 2) resumo.textContent = nomes.join(' · ');
            else resumo.textContent = nomes.length + ' viagens escolhidas';
            caixa.classList.toggle('tem-escolha', nomes.length > 0);
        }

        function filtrar() {
            var termo = semAcento(busca.value.trim());
            var algum = false;
            itens.forEach(function (l) {
                var bate = !termo || semAcento(l.textContent).indexOf(termo) !== -1;
                (l.parentElement || l).hidden = !bate;
                if (bate) algum = true;
            });
            nada.hidden = algum;
        }

        caixa.addEventListener('change', atualizarResumo);
        busca.addEventListener('input', filtrar);
        busca.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') e.preventDefault();
        });
        caixa.addEventListener('toggle', function () {
            if (caixa.open) busca.focus();
        });
        caixa.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && caixa.open) {
                caixa.open = false;
                caixa.querySelector('summary').focus();
            }
        });
        atualizarResumo();
    }

    document.addEventListener('click', function (e) {
        document.querySelectorAll('.escolha-suspensa[open]').forEach(function (caixa) {
            if (!caixa.contains(e.target)) caixa.open = false;
        });
    });

    function iniciar() {
        document.querySelectorAll('.escolha-suspensa').forEach(preparar);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
    else iniciar();
})();
