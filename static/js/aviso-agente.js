/* Pop-up de aviso aos agentes (templates/agencia/_aviso.html): abre sozinho e
   fecha no X, no Esc ou clicando fora da arte. */
(function () {
    var d = document.getElementById('avisoAgente');
    if (!d) return;
    function fechar() {
        if (typeof d.close === 'function') d.close(); else d.removeAttribute('open');
    }
    d.querySelector('.aviso-agente__fechar').addEventListener('click', fechar);
    d.addEventListener('click', function (e) { if (e.target === d) fechar(); });
    if (typeof d.showModal === 'function') d.showModal(); else d.setAttribute('open', '');
})();
