from django.urls import path
from django.views.generic import TemplateView # Importe o TemplateView direto do Django
from .views import (
    HomeView, ContatoView, TabelasView, SobreView, 
    CategoriaView, ProdutoDetalheView, AddCarrinhoView, 
    MeuCarrinhoView, ManipularCarrinhoView
)

app_name = "lojaapp"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contato/", ContatoView.as_view(), name="contato"),    
    path("tabelas/", TabelasView.as_view(), name="tabelas"),
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("todos-produtos/", CategoriaView.as_view(), name="todos-produtos"),
    path("produto/<slug:slug>/", ProdutoDetalheView.as_view(), name="produtodetalhe"),
    path("add-carrinho/<int:pro_id>/", AddCarrinhoView.as_view(), name="addcarrinho"),
    path("carrinho/", MeuCarrinhoView.as_view(), name="carrinho"),
    path("manipular-carrinho/<int:pro_id>/", ManipularCarrinhoView.as_view(), name="manipularcarrinho"),
    # Nova rota para o Checkout
    path("finalizar-pedido/", TemplateView.as_view(template_name="finalizar_pedido.html"), name="finalizarpedido"),
]
