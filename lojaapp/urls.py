from django.urls import path
from django.views.generic import TemplateView # Importe o TemplateView direto do Django
from .views import (
    HomeView, ContatoView, SobreView, 
    CategoriaView, ProdutoDetalheView, AddCarrinhoView, 
    MeuCarrinhoView, ManipularCarrinhoView, CheckoutView
)

app_name = "lojaapp"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contato/", ContatoView.as_view(), name="contato"),     
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("todos-produtos/", CategoriaView.as_view(), name="todos-produtos"),
    path("produto/<slug:slug>/", ProdutoDetalheView.as_view(), name="produtodetalhe"),
    path("add-carrinho/<int:pro_id>/", AddCarrinhoView.as_view(), name="addcarrinho"),
    path("carrinho/", MeuCarrinhoView.as_view(), name="carrinho"),
    path("manipular-carrinho/<int:pro_id>/", ManipularCarrinhoView.as_view(), name="manipularcarrinho"),
    path("finalizar-pedido/", CheckoutView.as_view(), name="finalizarpedido"),
]
