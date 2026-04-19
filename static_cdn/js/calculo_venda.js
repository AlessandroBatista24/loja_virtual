(function() {
    'use strict';
    window.addEventListener('load', function() {
        const ids = ['id_preco_custo', 'id_imposto_percentual', 'id_taxa_venda_percentual', 'id_custo_fixo_unidade', 'id_margem_desejada'];
        const campoVenda = document.getElementById('id_venda');

        function atualizarSimultaneamente() {
            const custo = parseFloat(document.getElementById('id_preco_custo').value) || 0;
            const imposto = parseFloat(document.getElementById('id_imposto_percentual').value) || 0;
            const taxa = parseFloat(document.getElementById('id_taxa_venda_percentual').value) || 0;
            const fixo = parseFloat(document.getElementById('id_custo_fixo_unidade').value) || 0;
            const margem = parseFloat(document.getElementById('id_margem_desejada').value) || 0;

            const totalTaxas = imposto + taxa + margem;

            if (totalTaxas < 100 && custo > 0) {
                const divisor = (100 - totalTaxas) / 100;
                const sugerido = (custo + fixo) / divisor;
                // Preenche o campo em tempo real
                campoVenda.value = Math.ceil(sugerido);
            }
        }

        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('input', atualizarSimultaneamente);
        });
    });
})();
