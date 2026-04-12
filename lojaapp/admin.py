from django.contrib import admin
from .models import Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, Pedido_order, Avaliacao
from django.utils.html import format_html # Importe aqui em cima para ficar limpo
from django.utils.safestring import mark_safe

class ProdutoAdmin(admin.ModelAdmin):
    # Isso faz a barra de pesquisa do Admin funcionar por Título e Descrição
    search_fields = ['titulo', 'discricao'] 
    list_display = ['titulo', 'categoria', 'venda', 'visualizacao']
    list_filter = ['categoria']

class CarrinhoProdutoInline(admin.TabularInline):
    model = CarrinhoProduto
    extra = 0
    readonly_fields = ('produto', 'quantidade', 'subtotal')

class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'total', 'criado_em']
    inlines = [CarrinhoProdutoInline]

class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'ordenado_por', 'total', 'pedido_status', 'criado_em']
    list_editable = ['pedido_status']
    list_filter = ['pedido_status', 'criado_em']
    
    # Atualize aqui: Remova 'endereco_envio' e coloque os novos campos
    readonly_fields = [
        'carrinho', 
        'ordenado_por', 
        'endereco',      # Novo campo
        'numero',        # Novo campo
        'complemento',   # Novo campo
        'bairro',        # Novo campo
        'cidade',        # Novo campo
        'estado',        # Novo campo
        'cep',           # Novo campo
        'telefone', 
        'email', 
        'subtotal', 
        'disconto', 
        'total', 
        'criado_em', 
        'exibir_produtos_detalhe'
    ]

    def exibir_produtos_detalhe(self, obj):
        # Busca os itens vinculados ao carrinho deste pedido
        produtos = obj.carrinho.carrinhoproduto_set.all()
        
        # Estilo inline para a tabela ficar com a cara do Admin do Django
        html = """
        <table style='width: 100%; border-collapse: collapse; border: 1px solid #ccc;'>
            <thead>
                <tr style='background-color: #417690; color: white;'>
                    <th style='padding: 10px; text-align: left;'>Produto</th>
                    <th style='padding: 10px; text-align: center;'>Qtd</th>
                    <th style='padding: 10px; text-align: right;'>Subtotal</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for p in produtos:
            html += f"""
                <tr style='border-bottom: 1px solid #eee;'>
                    <td style='padding: 10px;'>{p.produto.titulo}</td>
                    <td style='padding: 10px; text-align: center;'>{p.quantidade}</td>
                    <td style='padding: 10px; text-align: right;'>R$ {p.subtotal}</td>
                </tr>
            """
        
        html += "</tbody></table>"
        
        # O mark_safe permite que o Django renderize o HTML da tabela com segurança
        return mark_safe(html)

    # Nome que aparecerá na barra cinza acima da tabela no Admin
    exibir_produtos_detalhe.short_description = "Itens Comprados neste Pedido"


# Registros
admin.site.register(Cliente)
admin.site.register(Categoria)
admin.site.register(Produto, ProdutoAdmin) # Registra com a classe de busca
admin.site.register(Carrinho, CarrinhoAdmin)
admin.site.register(Pedido_order, PedidoAdmin)
admin.site.register(Avaliacao)
