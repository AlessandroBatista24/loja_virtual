from django.views.generic import TemplateView, View, CreateView, ListView, UpdateView
from django.shortcuts import render, redirect
from django.db.models import Avg 
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from .models import Produto, Categoria, Carrinho, CarrinhoProduto, Avaliacao, Pedido_order, Cliente, Cupom

User = get_user_model()


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all().order_by("titulo")
        
        query = self.request.GET.get('q')
        cat_slug = self.request.GET.get('categoria')

        # 1. Se houver busca por texto, filtra APENAS por texto
        if query:
            context["produto_list"] = Produto.objects.filter(titulo__icontains=query).order_by("-id")
        
        # 2. Se não houver texto, mas houver categoria, filtra por categoria
        elif cat_slug:
            context["produto_list"] = Produto.objects.filter(categoria__slug=cat_slug).order_by("-id")
            context["categoria_selecionada"] = Categoria.objects.get(slug=cat_slug)
        
        # 3. Se não houver nada, mostra tudo
        else:
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
        
        # BUSCA AS AVALIAÇÕES PARA EXIBIR NA TELA
        context["avaliacoes"] = Avaliacao.objects.filter(produto=produto_obj).order_by("-criado_em")
        
        return context

class AddCarrinhoView(View):
    def get(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        produto_obj = Produto.objects.get(id=pro_id)
        return render(request, "add_carrinho.html", {"produto": produto_obj})

    def post(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        produto_obj = Produto.objects.get(id=pro_id)
        quantidade = int(request.POST.get("quantidade", 1))

        # 1. Validação de estoque inicial
        if produto_obj.estoque < quantidade:
            return render(request, "add_carrinho.html", {
                "produto": produto_obj, 
                "erro": f"❌ Ops! Temos apenas {produto_obj.estoque} unidades em estoque."
            })

        # 2. Lógica de Carrinho Blindada (Busca ou Cria)
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = None

        if carrinho_id:
            carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first()
        
        if not carrinho_obj:
            carrinho_obj = Carrinho.objects.create(total=0)
            request.session["carrinho_id"] = carrinho_obj.id
            request.session.save() # Força a gravação imediata na sessão do navegador

        # 3. Adiciona ou atualiza o item no carrinho
        item, created = CarrinhoProduto.objects.get_or_create(
            carrinho=carrinho_obj,
            produto=produto_obj,
            defaults={'quantidade': quantidade, 'subtotal': produto_obj.venda * quantidade}
        )

        if not created:
            # Validação extra: Verifica se a soma (já no carrinho + nova qtd) supera o estoque
            if produto_obj.estoque < (item.quantidade + quantidade):
                return render(request, "add_carrinho.html", {
                    "produto": produto_obj, 
                    "erro": f"❌ Você já tem {item.quantidade} no carrinho. Limite de estoque: {produto_obj.estoque}."
                })
            
            item.quantidade += quantidade
            item.subtotal += (produto_obj.venda * quantidade)
            item.save()

        # 4. Atualiza o total geral do carrinho e salva
        carrinho_obj.total += (produto_obj.venda * quantidade)
        carrinho_obj.save()

        # 5. Redireciona para a página do carrinho (Retorna Status 302 no terminal)
        return redirect("lojaapp:carrinho")

class ContatoView(TemplateView):
    template_name = "contato.html"

@method_decorator(login_required(login_url="/login/"), name="dispatch")
class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        
        # BUSCAMOS O CLIENTE LOGADO (Para preencher o formulário automaticamente)
        cliente = request.user.cliente
        
        return render(request, "finalizar_pedido.html", {
            "carrinho": carrinho_obj,
            "cliente": cliente  # Enviamos o objeto cliente para o template
        })

    def post(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first()

        if not carrinho_obj:
            return redirect("lojaapp:home")

        # 1. Captura de dados do formulário
        nome = request.POST.get("ordenado_por")
        email = request.POST.get("email")
        tel = request.POST.get("telefone")
        end = request.POST.get("endereco")
        num = request.POST.get("numero")
        comp = request.POST.get("complemento")
        bair = request.POST.get("bairro")
        cid = request.POST.get("cidade")
        est = request.POST.get("estado")
        cep = request.POST.get("cep")

        # [OPCIONAL] Atualizar o endereço padrão do cliente com o que ele digitou agora
        cliente = request.user.cliente
        cliente.endereco = end
        cliente.numero = num
        cliente.bairro = bair
        cliente.cidade = cid
        cliente.estado = est
        cliente.cep = cep
        cliente.telefone = tel
        cliente.save()

        # 2. Lógica do Cupom
        cupom_codigo = request.POST.get("cupom")
        valor_desconto = 0
        if cupom_codigo:
            cupom = Cupom.objects.filter(codigo=cupom_codigo, ativo=True).first()
            if cupom:
                if carrinho_obj.total >= cupom.minimo_pedido:
                    valor_desconto = cupom.valor_desconto

        total_final = carrinho_obj.total - valor_desconto

        # 3. Criação do pedido e Baixa de Estoque
        try:
            novo_pedido = Pedido_order.objects.create(
                carrinho=carrinho_obj,
                ordenado_por=nome,
                email=email,
                telefone=tel,
                endereco=end,
                numero=num,
                complemento=comp,
                bairro=bair,
                cidade=cid,
                estado=est,
                cep=cep,
                subtotal=carrinho_obj.total,
                disconto=valor_desconto,
                total=total_final,
                pedido_status="Pedido Recebido"
            )

            # Baixa de estoque
            for cp in carrinho_obj.carrinhoproduto_set.all():
                produto = cp.produto
                produto.estoque -= cp.quantidade
                produto.save()

            if "carrinho_id" in request.session:
                del request.session["carrinho_id"]
                
            return render(request, "pagamento.html", {"pedido": novo_pedido})
            
        except Exception as e:
            return render(request, "finalizar_pedido.html", {"carrinho": carrinho_obj, "erro": str(e)})


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
   
class MeusPedidosView(LoginRequiredMixin, TemplateView):
    template_name = "meus_pedidos.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        # A assinatura deve ser EXATAMENTE (self, **kwargs)
        context = super().get_context_data(**kwargs)
        
        try:
            # O request já está disponível em self.request
            cliente = Cliente.objects.get(user=self.request.user)
            context["pedidos"] = Pedido_order.objects.filter(carrinho__cliente=cliente).order_by("-id")
        except Exception as e:
            context["pedidos"] = []
            
        return context

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas básicas
        context["total_pedidos"] = Pedido_order.objects.count()
        context["total_produtos"] = Produto.objects.count()
        context["estoque_baixo"] = Produto.objects.filter(estoque__lt=5)
        context["pedidos_recentes"] = Pedido_order.objects.all().order_by("-id")[:5]
        
        # SOMA DO FATURAMENTO (Excluindo cancelados)
        soma = Pedido_order.objects.exclude(pedido_status="Pedido Cancelado").aggregate(Sum('total'))['total__sum']
        context["faturamento_total"] = soma if soma else 0
        
        return context

class AdminProdutoCreateView(AdminRequiredMixin, CreateView):
    model = Produto
    template_name = "admin_produto_form.html"
    fields = ['titulo', 'slug', 'categoria', 'image', 'preco_mercado', 'venda', 'discricao', 'garantia', 'return_devolucao']
    success_url = "/admin-dashboard/" # Redireciona após salvar

class MeusDadosView(LoginRequiredMixin, TemplateView):
    template_name = "meus_dados.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # É ESSENCIAL passar o objeto cliente para o template aparecer
        context["cliente"] = self.request.user.cliente
        return context

    def post(self, request, *args, **kwargs):
        cliente = request.user.cliente
        # Salva os dados vindos do formulário
        cliente.endereco = request.POST.get("endereco")
        cliente.numero = request.POST.get("numero")
        cliente.bairro = request.POST.get("bairro")
        cliente.cidade = request.POST.get("cidade")
        cliente.estado = request.POST.get("estado")
        cliente.cep = request.POST.get("cep")
        cliente.telefone = request.POST.get("telefone")
        cliente.save()
        return redirect("lojaapp:meusdados")

# --- VIEW: MINHAS AVALIAÇÕES (Lista o que o cliente já comentou) ---
class MinhasAvaliacoesView(LoginRequiredMixin, ListView):
    template_name = "minhas_avaliacoes.html"
    context_object_name = "avaliacoes"

    def get_queryset(self):
        return Avaliacao.objects.filter(cliente=self.request.user.cliente).order_by("-criado_em")

# --- VIEW: AVALIAR PRODUTO (Lógica de envio) ---
class AvaliarProdutoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pro_id = self.kwargs.get("pro_id")
        produto = get_object_or_404(Produto, id=pro_id)
        cliente = self.request.user.cliente # Use self.request.user.cliente
        
        nota = request.POST.get("nota")
        comentario = request.POST.get("comentario")
        
        # Teste de terminal (apague depois)
        print(f"Salvando avaliação para {produto.titulo}: Nota {nota}")

        Avaliacao.objects.create(
            produto=produto,
            cliente=cliente,
            nota=nota,
            comentario=comentario
        )
        return redirect("lojaapp:produtodetalhe", slug=produto.slug)
