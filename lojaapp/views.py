from django.views.generic import TemplateView
from .models import Produto
from .models import Categoria

class HomeView(TemplateView):
    template_name = "home.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["produto_list"] = Produto.objects.all().order_by("-id")
        return context
    
class ProdutoView(TemplateView):
    template_name = "produto.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["todascategorias"] = Categoria.objects.all()
        return context
    
class ProdutoDetalheView(TemplateView):
    template_name = "produto_detalhe.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug'] # Pega o slug da URL
        context["produto"] = Produto.objects.get(slug=url_slug) # Busca o produto específico
        return context

class ContatoView(TemplateView):
    template_name = "contato.html"

class TabelasView(TemplateView):
    template_name = "tabelas.html"

class SobreView(TemplateView):
    template_name = "sobre.html"

class CategoriaView(TemplateView):
    template_name = "todos_produtos.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["todascategorias"] = Categoria.objects.all()
        return context

    