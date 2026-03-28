from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = "home.html"
    

class ContatoView(TemplateView):
    template_name = "contato.html"

class ImagemView(TemplateView):
    template_name = "imagem.html"

class TabelasView(TemplateView):
    template_name = "tabelas.html"

class SobreView(TemplateView):
    template_name = "sobre.html"