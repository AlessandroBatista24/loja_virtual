from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.db.models import Avg 
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# IMPORTANTE: Adicione o 'Cliente' na lista abaixo
from .models import Produto, Categoria, Carrinho, CarrinhoProduto, Avaliacao, Pedido_order, Cliente

# Define o User para ser usado na ClienteRegistroView
User = get_user_model()


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Pega o que o usuário digitou no campo 'q' do seu novo cabeçalho
        query = self.request.GET.get('q')
        
        if query:
            # 2. Filtra produtos onde o título contém o que foi digitado
            # O 'icontains' faz a busca ser inteligente (ignora maiúsculas/minúsculas)
            context["produto_list"] = Produto.objects.filter(
                titulo__icontains=query
            ).order_by("-id")
            
            # Adicionamos o termo de busca ao contexto para mostrar na tela se quiser
            context["termo_buscado"] = query
        else:
            # 3. Se não houver busca, mostra todos os produtos normalmente
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

@method_decorator(login_required(login_url="/login/"), name="dispatch")
class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        
        # Opcional: Se o usuário estiver logado, podemos tentar pré-preencher o nome
        # contexto = {"carrinho": carrinho_obj}
        return render(request, "finalizar_pedido.html", {"carrinho": carrinho_obj})


    def post(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first()

        if not carrinho_obj:
            return redirect("lojaapp:home")

        # 1. Captura de todos os NOVOS campos detalhados do HTML
        nome = request.POST.get("ordenado_por")
        email = request.POST.get("email")
        tel = request.POST.get("telefone")
        
        # Campos de endereço detalhados
        end = request.POST.get("endereco")
        num = request.POST.get("numero")
        comp = request.POST.get("complemento")
        bair = request.POST.get("bairro")
        cid = request.POST.get("cidade")
        est = request.POST.get("estado")
        cep = request.POST.get("cep")

        # 2. Criação do pedido com a nova estrutura do Model
        try:
            novo_pedido = Pedido_order.objects.create(
                carrinho=carrinho_obj,
                ordenado_por=nome,
                email=email,
                telefone=tel,
                endereco=end,        # Novo campo
                numero=num,          # Novo campo
                complemento=comp,    # Novo campo
                bairro=bair,         # Novo campo
                cidade=cid,          # Novo campo
                estado=est,          # Novo campo
                cep=cep,             # Novo campo
                subtotal=carrinho_obj.total,
                disconto=0,
                total=carrinho_obj.total,
                pedido_status="Pedido Recebido"
            )
            
            # 3. Limpa a sessão apenas se o pedido foi criado com sucesso
            if "carrinho_id" in request.session:
                del request.session["carrinho_id"]
            
            return render(request, "pagamento.html", {"pedido": novo_pedido})
            
        except Exception as e:
            # Mostra o erro exato no terminal para facilitar o conserto
            print(f"ERRO CRÍTICO AO SALVAR PEDIDO: {e}")
            return render(request, "finalizar_pedido.html", {
                "carrinho": carrinho_obj, 
                "erro": f"Erro técnico: {e}"
            })

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

class ClienteRegistroView(View):
    def get(self, request):
        return render(request, "registro.html")

    def post(self, request):
        # 1. Coleta os dados do formulário
        usuario = request.POST.get("username")
        email = request.POST.get("email")
        senha = request.POST.get("password")
        nome_c = request.POST.get("nome_completo")

        # 2. Verifica se o usuário já existe para não dar erro de integridade
        if User.objects.filter(username=usuario).exists():
            return render(request, "registro.html", {"erro": "Este nome de usuário já está em uso."})

        try:
            # 3. Cria o usuário oficial do Django
            novo_usuario = User.objects.create_user(usuario, email, senha)
            
            # 4. Cria o perfil do Cliente vinculado a esse usuário
            Cliente.objects.create(user=novo_usuario, nome_completo=nome_c)
            
            # 5. Faz o login automático e manda para a home
            login(request, novo_usuario)
            return redirect("lojaapp:home")
            
        except Exception as e:
            # Se der qualquer outro erro (ex: banco de dados fora do ar), avisa o usuário
            print(f"Erro no registro: {e}")
            return render(request, "registro.html", {"erro": "Ocorreu um erro ao criar sua conta. Tente novamente."})

# 2. View de Login
class ClienteLoginView(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        nome_usuario = request.POST.get("username")
        senha = request.POST.get("password")
        
        usuario = authenticate(username=nome_usuario, password=senha)
        
        if usuario is not None:
            login(request, usuario)
            return redirect("lojaapp:home")
        else:
            return render(request, "login.html", {"erro": "Usuário ou senha inválidos"})

# 3. View de Logout (Sair)
class ClienteLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("lojaapp:home")
    