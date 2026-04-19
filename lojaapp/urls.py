from django.urls import path
from .views import (
    HomeView, ContatoView, SobreView, MeusPedidosView,
    CategoriaView, ProdutoDetalheView, AddCarrinhoView, 
    MeuCarrinhoView, ManipularCarrinhoView, CheckoutView,
    ClienteRegistroView, ClienteLoginView, ClienteLogoutView, AdminDashboardView,
    AdminProdutoCreateView, MeusDadosView, MinhasAvaliacoesView, AvaliarProdutoView,
    EnderecoUpdateView, EnderecoCreateView, EnderecoDeleteView, AlterarSenhaView  
) # <--- Fechei o parêntese aqui

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
    
    # NOVAS ROTAS DE USUÁRIO
    path("registro/", ClienteRegistroView.as_view(), name="clienteregistro"),
    path("login/", ClienteLoginView.as_view(), name="clientelogin"),
    path("logout/", ClienteLogoutView.as_view(), name="clientelogout"),
    path("meus-pedidos/", MeusPedidosView.as_view(), name="meuspedidos"),
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admindashboard"),
    path("admin-produto/novo/", AdminProdutoCreateView.as_view(), name="adminprodutocreate"),
    path("meus-dados/", MeusDadosView.as_view(), name="meusdados"),
    path("minhas-avaliacoes/", MinhasAvaliacoesView.as_view(), name="minhasavaliacoes"),
    path("avaliar-produto/<int:pro_id>/", AvaliarProdutoView.as_view(), name="avaliarproduto"),
    path("alterar-senha/", AlterarSenhaView.as_view(), name="alterarsenha"),
    
    # ROTAS DE ENDEREÇO
    path("endereco/novo/", EnderecoCreateView.as_view(), name="enderecocreate"),
    path("endereco/editar/<int:pk>/", EnderecoUpdateView.as_view(), name="enderecoedit"),
    path("endereco/deletar/<int:pk>/", EnderecoDeleteView.as_view(), name="enderecodelete"), # Adicionada para evitar novos erros NoReverseMatch
]
