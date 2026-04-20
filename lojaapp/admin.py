from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, 
    Pedido_order, Avaliacao, PedidoRecebido, PedidoProcessando, 
    PedidoCaminho, PedidoFinalizado, Endereco, ImagemProduto, Cupom, Banner, MensagemContato
)
# --- 1. CONFIGURAÇÕES VISUAIS (INLINES) ---

class ImagemProdutoInline(admin.TabularInline):
    model = ImagemProduto
    extra = 3 

class CarrinhoProdutoInline(admin.TabularInline):
    model = CarrinhoProduto
    extra = 0
    readonly_fields = ('produto', 'quantidade', 'subtotal')

# --- 2. ADMINISTRAÇÃO DE PRODUTOS ---
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    # Organização visual dos campos
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'slug', 'categoria', 'image', 'discricao')
        }),
        ('Financeiro e Lucro Real', {
            'fields': (
                'preco_custo', 
                'imposto_percentual', 
                'taxa_venda_percentual', 
                'custo_fixo_unidade',
                'margem_desejada',
                'venda', 
                'preco_mercado'
            ),
            'description': '<b>Dica:</b> O preço de venda mudará em tempo real conforme você preenche os custos e a margem.',
        }),
        ('Estoque e Extras', {
            'fields': ('estoque', 'visualizacao', 'garantia', 'return_devolucao')
        }),
    )

    list_display = ['titulo', 'venda', 'preco_custo', 'lucro_liquido_real', 'margem_percentual', 'estoque']
    prepopulated_fields = {'slug': ('titulo',)}
    inlines = [ImagemProdutoInline]

    # --- ATIVA O CÁLCULO SIMULTÂNEO ---
    class Media:
        js = ('js/calculo_venda.js',)

    def lucro_liquido_real(self, obj):
        if obj.venda:
            imposto = (obj.venda * obj.imposto_percentual) / 100
            taxas = (obj.venda * obj.taxa_venda_percentual) / 100
            lucro = obj.venda - (obj.preco_custo + imposto + taxas + obj.custo_fixo_unidade)
            cor = "green" if lucro > 0 else "red"
            return format_html('<b style="color: {};">R$ {}</b>', cor, round(lucro, 2))
        return "Aguardando cálculo"

    def margem_percentual(self, obj):
        if obj.venda and obj.venda > 0:
            imposto = (obj.venda * obj.imposto_percentual) / 100
            taxas = (obj.venda * obj.taxa_venda_percentual) / 100
            lucro = obj.venda - (obj.preco_custo + imposto + taxas + obj.custo_fixo_unidade)
            margem = (lucro / obj.venda) * 100
            cor = "green" if margem > 0 else "red"
            return format_html('<span style="color: {};">{}%</span>', cor, round(margem, 2))
        return "0%"

    lucro_liquido_real.short_description = 'Lucro Líquido'
    margem_percentual.short_description = 'Margem %'

# --- 3. ADMINISTRAÇÃO DE PEDIDOS E CLIENTES ---

@admin.register(Pedido_order)
class PedidoAdmin(admin.ModelAdmin):
    # Adicionamos 'pagamento_status' e 'metodo_pagamento' na lista
    list_display = ['id', 'ordenado_por', 'total', 'status_pagamento_colorido', 'pedido_status', 'criado_em']
    list_editable = ['pedido_status']
    list_filter = ['pagamento_status', 'pedido_status', 'metodo_pagamento']
    search_fields = ['ordenado_por', 'id']

    def status_pagamento_colorido(self, obj):
        cores = {
            'Pago': 'green',
            'Pendente': '#E1AD01', # Amarelo/Dourado
            'Cancelado': 'red'
        }
        cor = cores.get(obj.pagamento_status, 'black')
        return format_html('<b style="color: {};">{}</b>', cor, obj.pagamento_status)
    
    status_pagamento_colorido.short_description = 'Status Pagto'

    # Mantém aquela tabela de produtos que você já tinha
    readonly_fields = ['exibir_produtos_detalhe']

    def exibir_produtos_detalhe(self, obj):
        produtos = obj.carrinho.carrinhoproduto_set.all()
        html = "<table style='width: 100%;'><thead><tr style='background:#417690;color:white;'><th>Produto</th><th>Qtd</th><th>Subtotal</th></tr></thead><tbody>"
        for p in produtos:
            html += f"<tr><td>{p.produto.titulo}</td><td>{p.quantidade}</td><td>R$ {p.subtotal}</td></tr>"
        return mark_safe(html + "</tbody></table>")
    
    exibir_produtos_detalhe.short_description = "Itens do Pedido"


# --- 4. ABAS ORGANIZADAS DE PEDIDOS (PROXY) ---

class PedidoBaseAdmin(PedidoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-id')

@admin.register(PedidoRecebido)
class PedidoRecebidoAdmin(PedidoBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(pedido_status="Pedido Recebido")

@admin.register(PedidoProcessando)
class PedidoProcessandoAdmin(PedidoBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(pedido_status="Pedido Processando")

@admin.register(PedidoCaminho)
class PedidoCaminhoAdmin(PedidoBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(pedido_status="Pedido Caminho")

@admin.register(PedidoFinalizado)
class PedidoFinalizadoAdmin(PedidoBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(pedido_status="Pedido Finalizado")

# --- 5. DEMAIS REGISTROS ---

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'slug']
    prepopulated_fields = {'slug': ('titulo',)}

@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'data_envio']
    readonly_fields = ['nome', 'email', 'mensagem', 'data_envio'] 

@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'total', 'criado_em']
    inlines = [CarrinhoProdutoInline]

admin.site.register(Cliente)
admin.site.register(Avaliacao)
admin.site.register(Endereco)
admin.site.register(Cupom)
admin.site.register(Banner)

