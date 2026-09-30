/* Soar Operadora — máscaras de telefone, CEP, CNPJ, CADASTUR e preço em reais.

   A pessoa digita só os números; os parênteses, pontos, barra e traço entram
   sozinhos. Vale para todo campo com data-mascara="telefone|cep|cnpj|cadastur".
   No painel do dono (admin do Django) os campos não têm esse atributo, então
   eles são reconhecidos pelo nome.

   O servidor confere e formata de novo (soar/mascaras.py): a máscara aqui é
   conforto de quem digita, não a garantia. */
(function () {
    'use strict';

    function digitos(valor) { return (valor || '').replace(/\D/g, ''); }

    var FORMATOS = {
        telefone: function (v) {
            var n = digitos(v);
            if (n.length > 11 && n.indexOf('55') === 0) { n = n.slice(2); }
            n = n.slice(0, 11);
            if (!n) { return ''; }
            if (n.length <= 2) { return '(' + n; }
            var ddd = n.slice(0, 2), resto = n.slice(2);
            // celular (9 dígitos) e fixo (8 dígitos): o traço fica antes dos 4 últimos
            var corte = resto.length > 8 ? 5 : 4;
            if (resto.length <= corte) { return '(' + ddd + ') ' + resto; }
            return '(' + ddd + ') ' + resto.slice(0, corte) + '-' + resto.slice(corte);
        },
        cep: function (v) {
            return juntar(digitos(v).slice(0, 8), [[5, '-'], [3, '']]);
        },
        cnpj: function (v) {
            var n = digitos(v).slice(0, 14);
            return juntar(n, [[2, '.'], [3, '.'], [3, '/'], [4, '-'], [2, '']]);
        },
        cadastur: function (v) {
            var n = digitos(v).slice(0, 15);
            return juntar(n, [[2, '.'], [6, '.'], [2, '.'], [4, '-'], [1, '']]);
        }
    };

    /* Corta os números em blocos e cola o separador depois de cada bloco
       completo (só depois: assim apagar com backspace não trava no ponto). */
    function juntar(n, blocos) {
        var saida = '', i = 0;
        for (var b = 0; b < blocos.length && i < n.length; b++) {
            var pedaco = n.slice(i, i + blocos[b][0]);
            i += pedaco.length;
            saida += pedaco;
            if (i < n.length) { saida += blocos[b][1]; }
        }
        return saida;
    }

    function aplicar(campo, tipo) {
        if (campo.dataset.mascaraPronta) { return; }
        campo.dataset.mascaraPronta = '1';
        var formatar = FORMATOS[tipo];
        if (!campo.getAttribute('inputmode')) { campo.setAttribute('inputmode', 'numeric'); }
        campo.addEventListener('input', function () {
            // mantém o cursor no fim do que já foi digitado
            var antes = digitos(campo.value.slice(0, campo.selectionStart)).length;
            campo.value = formatar(campo.value);
            var pos = 0, contados = 0;
            while (pos < campo.value.length && contados < antes) {
                if (/\d/.test(campo.value[pos])) { contados++; }
                pos++;
            }
            campo.setSelectionRange(pos, pos);
        });
        if (campo.value) { campo.value = formatar(campo.value); }
    }

    /* Preço em reais: "3500" vira "3.500" enquanto digita e "3.500,00" ao sair
       do campo. A vírgula é digitada pela pessoa e separa os centavos (no
       máximo 2). Vale para todo campo com a classe preco-brl, que é a do
       CampoPreco (destinations/admin.py): preço do destino, também na lista,
       e valor do orçamento da agência. O servidor lê "3.500,00", "3500" e
       "R$ 3.500" do mesmo jeito, então a máscara é só conforto. */
    function formatarMoeda(valor) {
        var limpo = (valor || '').replace(/[^\d,]/g, '');
        var virgula = limpo.indexOf(',');
        var inteiro = virgula === -1 ? limpo : limpo.slice(0, virgula);
        var centavos = virgula === -1 ? null : limpo.slice(virgula + 1).replace(/,/g, '').slice(0, 2);
        inteiro = inteiro.replace(/^0+(?=\d)/, '');
        if (!inteiro && centavos !== null) { inteiro = '0'; }
        inteiro = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return centavos === null ? inteiro : inteiro + ',' + centavos;
    }

    function completarCentavos(valor) {
        if (!valor) { return ''; }
        var partes = valor.split(',');
        var centavos = ((partes[1] || '') + '00').slice(0, 2);
        return (partes[0] || '0') + ',' + centavos;
    }

    function aplicarMoeda(campo) {
        if (campo.dataset.mascaraPronta) { return; }
        campo.dataset.mascaraPronta = '1';
        campo.setAttribute('inputmode', 'decimal');
        campo.addEventListener('input', function () {
            // Devolve o cursor contando o que vem DEPOIS dele: a máscara mexe
            // no começo (pontos, o "0" de ",75"), nunca no fim.
            var depois = campo.value.slice(campo.selectionEnd).replace(/[^\d,]/g, '').length;
            campo.value = formatarMoeda(campo.value);
            var pos = campo.value.length, contados = 0;
            while (pos > 0 && contados < depois) {
                pos--;
                if (/[\d,]/.test(campo.value[pos])) { contados++; }
            }
            campo.setSelectionRange(pos, pos);
        });
        campo.addEventListener('blur', function () {
            campo.value = completarCentavos(formatarMoeda(campo.value));
        });
        if (campo.value) { campo.value = completarCentavos(formatarMoeda(campo.value)); }
    }

    var moedas = function (raiz) {
        raiz.querySelectorAll('input.preco-brl, input[data-mascara="moeda"]').forEach(aplicarMoeda);
    };
    moedas(document);
    document.addEventListener('formset:added', function (e) { moedas(e.target); });

    document.querySelectorAll('input[data-mascara]').forEach(function (campo) {
        if (FORMATOS[campo.dataset.mascara]) { aplicar(campo, campo.dataset.mascara); }
    });

    /* Painel do dono: telefone da reserva e do orçamento, WhatsApp e CADASTUR
       da agência. O CNPJ fica de fora aqui porque o painel guarda só os 14
       números nesse campo. Os blocos de "adicionar outro" também entram. */
    if (document.getElementById('site-name')) {
        var porNome = function (raiz) {
            raiz.querySelectorAll('input[type="text"]').forEach(function (campo) {
                var nome = campo.name || '';
                if (/(^|-)(telefone|cliente_telefone|whatsapp)$/.test(nome)) { aplicar(campo, 'telefone'); }
                else if (/(^|-)cadastur$/.test(nome)) { aplicar(campo, 'cadastur'); }
            });
        };
        porNome(document);
        document.addEventListener('formset:added', function (e) { porNome(e.target); });
    }
})();
