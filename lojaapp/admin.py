from django.contrib import admin
from .models import Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, Pedido_order, Avaliacao

# 1. Configuração para exibir os produtos DENTRO da página do Carrinho
class CarrinhoProdutoInline(admin.TabularInline):
    model = CarrinhoProduto
    extra = 0 # Não mostra linhas vazias extras
    readonly_fields = ('produto', 'quantidade', 'subtotal')

# 2. Configuração da página de Carrinho no Admin
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'total', 'criado_em'] # Colunas que aparecem na lista
    list_filter = ['criado_em'] # Filtro lateral por data
    inlines = [CarrinhoProdutoInline] # ATIVA a visualização dos itens dentro do carrinho

# 3. Configuração da página de Pedidos
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'ordenado_por', 'total', 'pedido_status', 'criado_em']
    list_editable = ['pedido_status'] # Permite mudar o status direto na lista
    list_filter = ['pedido_status', 'criado_em']

# Registros individuais
admin.site.register(Cliente)
admin.site.register(Categoria)
admin.site.register(Produto)
admin.site.register(Carrinho, CarrinhoAdmin) # Usa a configuração especial
admin.site.register(Pedido_order, PedidoAdmin) # Usa a configuração especial

# Opcional: Registrar o CarrinhoProduto sozinho também, se quiser
admin.site.register(CarrinhoProduto)
admin.site.register(Avaliacao)
