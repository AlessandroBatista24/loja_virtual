from django.urls import path
from .views import HomeView, ContatoView, ImagemView, TabelasView, SobreView



app_name = "lojaapp"

urlpatterns = [
    # Aspas vazias significam a "página inicial" da loja
    # Precisamos da vírgula depois das aspas
    path("", HomeView.as_view(), name="home"),
    path("contato/", ContatoView.as_view(), name="contato"),
    path("imagem/", ImagemView.as_view(), name="imagem"),
    path("tabelas/", TabelasView.as_view(), name="tabelas"),
    path("sobre/", SobreView.as_view(), name="sobre")
]