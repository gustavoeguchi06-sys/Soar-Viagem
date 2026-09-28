/* Trava o formulário enquanto ele é enviado.

   Sem isso, um clique duplo (ou a pessoa apertando de novo porque a internet
   está lenta) mandava o mesmo pedido duas vezes: reserva, orçamento ou
   cadastro repetido. O servidor também se protege, mas o botão travado evita
   que o segundo envio chegue a sair.

   Vale só para formulários POST. A busca (GET) não muda nada no servidor, e
   travá-la só atrapalharia quem volta pelo botão "Voltar" do navegador.
   Um POST que devolve arquivo para baixar (a página não muda) deve levar
   `data-sem-trava`, senão o botão fica travado depois do download.

   O ouvinte fica no `document`: ele roda depois dos ouvintes do próprio
   formulário (como o "Tem certeza?" do cancelar reserva), então quando a
   pessoa responde "Cancelar" no aviso nada é travado. */
(function () {
    'use strict';

    function travar(form, quemEnviou) {
        // Um botão desativado não vai junto no envio. Se o botão clicado tem
        // nome (ex.: "salvar e continuar"), o valor dele segue num campo oculto.
        if (quemEnviou && quemEnviou.name) {
            var copia = document.createElement('input');
            copia.type = 'hidden';
            copia.name = quemEnviou.name;
            copia.value = quemEnviou.value;
            copia.setAttribute('data-envio-copia', '');
            form.appendChild(copia);
        }
        form.setAttribute('data-enviando', '');
        form.setAttribute('aria-busy', 'true');
        form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]')
            .forEach(function (botao) {
                if (botao.disabled) { return; }         // já estava desativado: não é nosso
                botao.disabled = true;
                botao.setAttribute('data-travado', '');
            });
    }

    function destravar(form) {
        form.removeAttribute('data-enviando');
        form.removeAttribute('aria-busy');
        form.querySelectorAll('[data-envio-copia]').forEach(function (campo) { campo.remove(); });
        form.querySelectorAll('[data-travado]').forEach(function (botao) {
            botao.disabled = false;
            botao.removeAttribute('data-travado');
        });
    }

    document.addEventListener('submit', function (evento) {
        var form = evento.target;
        if ((form.getAttribute('method') || 'get').toLowerCase() !== 'post') { return; }
        if (form.hasAttribute('data-sem-trava')) { return; }   // ex.: form que baixa arquivo
        if (form.hasAttribute('data-enviando')) {      // já saiu uma vez
            evento.preventDefault();
            return;
        }
        if (evento.defaultPrevented) { return; }       // o "Tem certeza?" foi recusado
        travar(form, evento.submitter);
    });

    // Quem volta pelo botão "Voltar" recebe a página do cache do navegador,
    // ainda com o botão travado. Aqui ele é liberado de novo.
    window.addEventListener('pageshow', function () {
        document.querySelectorAll('form[data-enviando]').forEach(destravar);
    });
}());
