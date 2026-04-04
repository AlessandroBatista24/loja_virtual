from django.urls import path
# Adicione CategoriaView aqui embaixo:
from .views import HomeView, ContatoView, TabelasView, SobreView, CategoriaView, ProdutoDetalheView, AddCarrinhoView, MeuCarrinhoView

app_name = "lojaapp"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contato/", ContatoView.as_view(), name="contato"),    
    path("tabelas/", TabelasView.as_view(), name="tabelas"),
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("todos-produtos/", CategoriaView.as_view(), name="todos-produtos"),
    path("produto/<slug:slug>/", ProdutoDetalheView.as_view(), name="produtodetalhe"),
    path("addcarrinho-<int:pro_id>/", AddCarrinhoView.as_view(), name="addcarrinho"),
    path("carrinho/", MeuCarrinhoView.as_view(), name="carrinho")
]
