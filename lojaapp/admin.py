from django.contrib import admin
from .models import (
    Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, 
    Pedido_order, Avaliacao, PedidoRecebido, PedidoProcessando, 
    PedidoCaminho, PedidoFinalizado, Endereco, ImagemProduto, Cupom, Banner
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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
    inlines = [ImagemProdutoInline]
    
# --- 3. ADMINISTRAÇÃO DE PEDIDOS E CLIENTES ---

@admin.register(Pedido_order)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'ordenado_por', 'total', 'pedido_status', 'criado_em']
    list_editable = ['pedido_status']
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

@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'total', 'criado_em']
    inlines = [CarrinhoProdutoInline]

admin.site.register(Cliente)
admin.site.register(Avaliacao)
admin.site.register(Endereco)
admin.site.register(Cupom)
admin.site.register(Banner)

