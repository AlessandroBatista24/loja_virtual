from django.contrib import admin
# Use o espaço correto aqui: from .models (com ponto)
from .models import Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, Pedido_order

# Registre passando uma LISTA (com colchetes)
admin.site.register([Cliente, Categoria, Produto, Carrinho, CarrinhoProduto, Pedido_order])
