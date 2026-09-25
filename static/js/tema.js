/* Soar Operadora — tema claro/escuro, aplicado antes da página aparecer.
   Carrega no <head>, sem defer, para a página não piscar clara e depois
   escurecer. A chave "theme" é a mesma do painel do dono (Django admin), então
   quem escolhe o escuro num lado vê o escuro no outro. Sem escolha, fica claro;
   "auto" (que só o painel grava) segue o sistema. */
(function () {
    var escolha = null;
    try { escolha = localStorage.getItem('theme'); } catch (e) { /* navegação privada */ }
    var escuro = escolha === 'dark' || (escolha === 'auto' && window.matchMedia &&
                 window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.setAttribute('data-tema', escuro ? 'escuro' : 'claro');
})();
