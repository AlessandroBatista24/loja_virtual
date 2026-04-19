(function($) {
    'use strict';
    $(document).ready(function() {
        const inputs = ['#id_preco_custo', '#id_imposto_percentual', '#id_taxa_venda_percentual', '#id_custo_fixo_unidade', '#id_margem_desejada'];
        const $venda = $('#id_venda');

        function calcular() {
            const custo = parseFloat($('#id_preco_custo').val()) || 0;
            const imposto = parseFloat($('#id_imposto_percentual').val()) || 0;
            const taxa = parseFloat($('#id_taxa_venda_percentual').val()) || 0;
            const fixo = parseFloat($('#id_custo_fixo_unidade').val()) || 0;
            const margem = parseFloat($('#id_margem_desejada').val()) || 0;

            const somaPercentuais = imposto + taxa + margem;

            if (somaPercentuais < 100 && custo > 0) {
                const divisor = (100 - somaPercentuais) / 100;
                const sugerido = (custo + fixo) / divisor;
                $venda.val(Math.ceil(sugerido));
            }
        }

        // Attiva il calcolo su ogni cambiamento
        $(inputs.join(',')).on('input change', calcular);
        
        // Esegue il calcolo all'avvio
        setTimeout(calcular, 500); 
    });
})(django.jQuery);
