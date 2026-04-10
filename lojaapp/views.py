from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.db.models import Avg 
# Importação corrigida com Pedido_order incluso
from .models import Produto, Categoria, Carrinho, CarrinhoProduto, Avaliacao, Pedido_order
from .forms import CheckoutForm

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
        url_slug = self.kwargs['slug']        
        produto_obj = Produto.objects.get(slug=url_slug)       
        
        # Incrementa visualização
        produto_obj.visualizacao += 1
        produto_obj.save()       
        
        context["produto"] = produto_obj
        # Busca todas as avaliações deste produto
        context["avaliacoes"] = Avaliacao.objects.filter(produto=produto_obj).order_by("-criado_em")
        # Calcula a média (opcional)
        context["media_notas"] = Avaliacao.objects.filter(produto=produto_obj).aggregate(Avg('nota'))['nota__avg']
        
        return context

    
class AddCarrinhoView(View):
    # O método GET apenas mostra a página de confirmação
    def get(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        produto_obj = Produto.objects.get(id=pro_id)
        return render(request, "add_carrinho.html", {"produto": produto_obj})

    # O método POST salva os dados no Banco de Dados
    def post(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        produto_obj = Produto.objects.get(id=pro_id)
        quantidade = int(request.POST.get("quantidade", 1))

        # 1. Busca ou cria o carrinho na sessão do navegador
        carrinho_id = request.session.get("carrinho_id", None)
        if carrinho_id:
            try:
                carrinho_obj = Carrinho.objects.get(id=carrinho_id)
            except Carrinho.DoesNotExist:
                carrinho_obj = Carrinho.objects.create(total=0)
                request.session["carrinho_id"] = carrinho_obj.id
        else:
            carrinho_obj = Carrinho.objects.create(total=0)
            request.session["carrinho_id"] = carrinho_obj.id

        # 2. Adiciona o produto ou aumenta a quantidade se já existir
        item, created = CarrinhoProduto.objects.get_or_create(
            carrinho=carrinho_obj,
            produto=produto_obj,
            defaults={'quantidade': quantidade, 'subtotal': produto_obj.venda * quantidade}
        )

        if not created:
            item.quantidade += quantidade
            item.subtotal += (produto_obj.venda * quantidade)
            item.save()

        # 3. Atualiza o total geral do carrinho
        carrinho_obj.total += (produto_obj.venda * quantidade)
        carrinho_obj.save()

        # Após salvar, redireciona para a Home (ou para a página do Carrinho)
        return redirect("lojaapp:home")

class ContatoView(TemplateView):
    template_name = "contato.html"

class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        return render(request, "finalizar_pedido.html", {"carrinho": carrinho_obj})

    def post(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first()

        if not carrinho_obj:
            return redirect("lojaapp:home")

        # Pega os dados que o usuário digitou
        nome = request.POST.get("ordenado_por")
        email = request.POST.get("email")
        tel = request.POST.get("telefone")
        endereco = request.POST.get("endereco_envio")

        # CRIA O PEDIDO NO BANCO
        try:
            novo_pedido = Pedido_order.objects.create(
                carrinho=carrinho_obj,
                ordenado_por=nome,
                endereco_envio=endereco,
                telefone=tel,
                email=email,
                subtotal=carrinho_obj.total,
                disconto=0,
                total=carrinho_obj.total,
                pedido_status="Pedido Recebido"
            )
            
            # Limpa o carrinho da sessão apenas DEPOIS de salvar o pedido
            del request.session["carrinho_id"]
            
            # Redireciona para a página de sucesso/pagamento
            return render(request, "pagamento.html", {"pedido": novo_pedido})
            
        except Exception as e:
            print(f"Erro ao salvar pedido: {e}")
            return render(request, "finalizar_pedido.html", {"carrinho": carrinho_obj, "erro": "Erro ao processar pedido."})


class MeuCarrinhoView(TemplateView):
    template_name = "meu_carrinho.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrinho_id = self.request.session.get("carrinho_id", None)
        if carrinho_id:
            try:
                carrinho_obj = Carrinho.objects.get(id=carrinho_id)
                context["carrinho"] = carrinho_obj
            except Carrinho.DoesNotExist:
                context["carrinho"] = None
        else:
            context["carrinho"] = None
        return context

class SobreView(TemplateView):
    template_name = "sobre.html"

class ManipularCarrinhoView(View):
    def get(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        acao = request.GET.get("acao")
        carrinho_id = request.session.get("carrinho_id")
        
        if carrinho_id:
            try:
                carrinho_obj = Carrinho.objects.get(id=carrinho_id)
                
                # Ação de Limpar Carrinho Inteiro
                if acao == "limpar":
                    carrinho_obj.delete()
                    if "carrinho_id" in request.session:
                        del request.session["carrinho_id"]
                
                else:
                    # Ações de Itens Individuais (+, -, rmv)
                    produto_obj = Produto.objects.get(id=pro_id)
                    item = CarrinhoProduto.objects.filter(carrinho=carrinho_obj, produto=produto_obj).first()
                    
                    if item:
                        if acao == "inc":
                            item.quantidade += 1
                            item.subtotal += produto_obj.venda
                            item.save()
                            carrinho_obj.total += produto_obj.venda
                        
                        elif acao == "dec":
                            if item.quantidade > 1:
                                item.quantidade -= 1
                                item.subtotal -= produto_obj.venda
                                item.save()
                                carrinho_obj.total -= produto_obj.venda
                            else:
                                carrinho_obj.total -= item.subtotal
                                item.delete()
                        
                        elif acao == "rmv":
                            carrinho_obj.total -= item.subtotal
                            item.delete()
                        
                        carrinho_obj.save()

                # Se após as alterações de itens o carrinho ficou vazio, removemos ele
                if carrinho_id and Carrinho.objects.filter(id=carrinho_id).exists():
                    if not carrinho_obj.carrinhoproduto_set.exists():
                        carrinho_obj.delete()
                        if "carrinho_id" in request.session:
                            del request.session["carrinho_id"]

            except (Carrinho.DoesNotExist, Produto.DoesNotExist):
                pass
                
        return redirect("lojaapp:carrinho")
    
class CategoriaView(TemplateView):
    template_name = "todos_produtos.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["todascategorias"] = Categoria.objects.all()
        return context


    