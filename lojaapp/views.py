from django.views.generic import TemplateView, View, CreateView, ListView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Avg, Sum, Q # Aggiunto Q per filtri complessi
from django.db import transaction 
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import mercadopago
from .models import (
    Produto, Categoria, Carrinho, CarrinhoProduto, 
    Avaliacao, Pedido_order, Cliente, Cupom, Endereco, Banner, ImagemProduto, MensagemContato
)

User = get_user_model()

@csrf_exempt
def webhook_mercadopago(request):
    # O Mercado Pago envia um ID de pagamento via parâmetro na URL ou no corpo
    payment_id = request.GET.get('data.id') or request.POST.get('data.id')
    
    if payment_id:
        sdk = mercadopago.SDK("SEU_ACCESS_TOKEN_AQUI")
        payment_info = sdk.payment().get(payment_id)
        
        # Pega o ID do pedido que salvamos no 'external_reference'
        pedido_id = payment_info["response"]["external_reference"]
        status = payment_info["response"]["status"]

        if status == "approved":
            pedido = Pedido_order.objects.get(id=pedido_id)
            pedido.pagamento_status = "Pago"
            pedido.pagamento_confirmado = True
            pedido.save()
            
    return HttpResponse(status=200)

# ============================================================
# NAVEGAÇÃO E PRODUTOS
# ============================================================

class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all().order_by("titulo")
        
        # --- ADICIONE ESTA LINHA AQUI ---
        context["banners"] = Banner.objects.filter(ativo=True) 
        # -------------------------------

        query = self.request.GET.get('q')
        cat_slug = self.request.GET.get('categoria')

        if query:
            qs = Produto.objects.filter(Q(titulo__icontains=query) | Q(discricao__icontains=query))
        elif cat_slug:
            qs = Produto.objects.filter(categoria__slug=cat_slug)
            context["categoria_selecionada"] = Categoria.objects.get(slug=cat_slug)
        else:
            qs = Produto.objects.all()

        context["produto_list"] = qs.order_by("-id")[:15]
        return context

class CategoriaView(TemplateView):
    template_name = "todos_produtos.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["todascategorias"] = Categoria.objects.all()
        return context

class ProdutoDetalheView(TemplateView):
    template_name = "produto_detalhe.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_obj = get_object_or_404(Produto, slug=self.kwargs['slug'])       
        
        produto_obj.visualizacao += 1
        produto_obj.save()

        pode_avaliar = False
        ja_avaliou = False

        if self.request.user.is_authenticated:
            cliente, _ = Cliente.objects.get_or_create(user=self.request.user)
            
            # BUSCA DIRETA NO PEDIDO (Ignora falhas no vínculo do carrinho)
            # Verifica se existe algum pedido finalizado deste cliente que contenha o produto
            pode_avaliar = Pedido_order.objects.filter(
                carrinho__cliente=cliente,
                carrinho__carrinhoproduto__produto=produto_obj,
                pedido_status="Pedido Finalizado"
            ).exists()

            # SE AINDA ASSIM NÃO ACHAR (Caso o carrinho esteja sem cliente), 
            # tentamos pelo email do pedido
            if not pode_avaliar:
                pode_avaliar = Pedido_order.objects.filter(
                    email=self.request.user.email,
                    carrinho__carrinhoproduto__produto=produto_obj,
                    pedido_status="Pedido Finalizado"
                ).exists()
            
            ja_avaliou = Avaliacao.objects.filter(produto=produto_obj, cliente=cliente).exists()
        
        context.update({
            "produto": produto_obj,
            "pode_avaliar": pode_avaliar,
            "ja_avaliou": ja_avaliou,
            "avaliacoes": Avaliacao.objects.filter(produto=produto_obj).order_by("-criado_em")
        })
        return context


# ============================================================
# CARRINHO
# ============================================================

class AddCarrinhoView(View):
    def get(self, request, *args, **kwargs):
        produto_obj = get_object_or_404(Produto, id=self.kwargs['pro_id'])
        return render(request, "add_carrinho.html", {"produto": produto_obj})

    def post(self, request, *args, **kwargs):
        produto_obj = get_object_or_404(Produto, id=self.kwargs['pro_id'])
        try:
            quantidade = int(request.POST.get("quantidade", 1))
            if quantidade < 1: raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Quantidade inválida.")
            return redirect("lojaapp:produtodetalhe", slug=produto_obj.slug)

        if produto_obj.estoque < quantidade:
            messages.error(request, f"❌ Estoque insuficiente. Temos apenas {produto_obj.estoque} unidades.")
            return redirect("lojaapp:produtodetalhe", slug=produto_obj.slug)

        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        
        if not carrinho_obj:
            carrinho_obj = Carrinho.objects.create(total=0)
            request.session["carrinho_id"] = carrinho_obj.id

        # Logica di aggiornamento professionale: ricalcola sempre basandosi sul prezzo attuale del DB
        item, created = CarrinhoProduto.objects.get_or_create(
            carrinho=carrinho_obj, 
            produto=produto_obj,
            defaults={'quantidade': quantidade, 'subtotal': produto_obj.venda * quantidade}
        )

        if not created:
            item.quantidade += quantidade
            item.subtotal = item.quantidade * produto_obj.venda # Protezione prezzo
            item.save()

        # Ricalcolo totale carrello granulare
        carrinho_obj.total = carrinho_obj.carrinhoproduto_set.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
        carrinho_obj.save()
        
        messages.success(request, f"✅ {produto_obj.titulo} adicionado ao carrinho!")
        return redirect("lojaapp:carrinho")

class ManipularCarrinhoView(View):
    def get(self, request, *args, **kwargs):
        pro_id = self.kwargs['pro_id']
        acao = request.GET.get("acao")
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        
        if carrinho_obj:
            if acao == "limpar":
                carrinho_obj.delete()
                del request.session["carrinho_id"]
            else:
                produto_obj = get_object_or_404(Produto, id=pro_id)
                item = CarrinhoProduto.objects.filter(carrinho=carrinho_obj, produto=produto_obj).first()
                if item:
                    if acao == "inc" and produto_obj.estoque > item.quantidade:
                        item.quantidade += 1
                        item.subtotal = item.quantidade * produto_obj.venda
                        item.save()
                    elif acao == "dec":
                        if item.quantidade > 1:
                            item.quantidade -= 1
                            item.subtotal = item.quantidade * produto_obj.venda
                            item.save()
                        else: item.delete()
                    elif acao == "rmv": item.delete()

                carrinho_obj.total = carrinho_obj.carrinhoproduto_set.aggregate(Sum('subtotal'))['subtotal__sum'] or 0
                carrinho_obj.save()
        return redirect("lojaapp:carrinho")

@method_decorator(login_required(login_url="/login/"), name="dispatch")
class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first() if carrinho_id else None
        
        # Garante que o cliente existe
        cliente, _ = Cliente.objects.get_or_create(
            user=request.user, 
            defaults={'nome_completo': request.user.username}
        )
        
        # BUSCA OS ENDEREÇOS
        enderecos = Endereco.objects.filter(cliente=cliente).order_by('-padrao')
        
        print(f"\n✅ CHECKOUT GET: Enviando {enderecos.count()} endereços para {request.user.username}\n")

        return render(request, "finalizar_pedido.html", {
            "carrinho": carrinho_obj, 
            "enderecos": enderecos,
            "cliente": cliente
        })

    def post(self, request, *args, **kwargs):
        carrinho_id = request.session.get("carrinho_id")
        carrinho_obj = get_object_or_404(Carrinho, id=carrinho_id)
        
        endereco_id = request.POST.get("endereco_selecionado")
        metodo_pagto = request.POST.get("metodo_pagamento", "Pix")

        if not endereco_id:
            messages.error(request, "Por favor, selecione um endereço.")
            return redirect("lojaapp:finalizarpedido")
            
        endereco_obj = get_object_or_404(Endereco, id=endereco_id, cliente__user=request.user)
        cliente = request.user.cliente

        try:
            with transaction.atomic():
                # 1. Cria o Pedido (Mantenha como você já tem)
                novo_pedido = Pedido_order.objects.create(
                    carrinho=carrinho_obj, 
                    ordenado_por=cliente.nome_completo,
                    endereco=endereco_obj.rua, 
                    numero=endereco_obj.numero,
                    bairro=endereco_obj.bairro, 
                    cidade=endereco_obj.cidade,
                    estado=endereco_obj.estado, 
                    cep=endereco_obj.cep,
                    telefone=cliente.telefone or "", 
                    email=request.user.email,
                    subtotal=carrinho_obj.total, 
                    disconto=0, 
                    total=carrinho_obj.total,
                    pedido_status="Pedido Recebido",
                    metodo_pagamento=metodo_pagto,
                    pagamento_status="Pendente"
                )

                # 2. Configura Mercado Pago
                # VERIFIQUE SE O TOKEN ABAIXO É O "ACCESS TOKEN" (NÃO É O PUBLIC KEY)
                sdk = mercadopago.SDK("SEU_ACCESS_TOKEN_REAL_AQUI")
                
                preference_data = {
                    "items": [
                        {
                            "title": f"Pedido #{novo_pedido.id}",
                            "quantity": 1,
                            "unit_price": float(novo_pedido.total),
                            "currency_id": "BRL"
                        }
                    ],
                    "external_reference": str(novo_pedido.id),
                    "back_urls": {
                        "success": request.build_absolute_uri(reverse_lazy('lojaapp:home')),
                        "failure": request.build_absolute_uri(reverse_lazy('lojaapp:carrinho')),
                    },
                    "auto_return": "approved",
                }
                
                # CHAMADA À API
                preference_response = sdk.preference().create(preference_data)

                # --- VALIDAÇÃO CRÍTICA DO NONE ---
                if not preference_response or "response" not in preference_response:
                    print(f"❌ RESPOSTA VAZIA DA API: {preference_response}")
                    raise Exception("O Mercado Pago não respondeu. Verifique sua conexão e o Access Token.")

                # Agora é seguro tentar o .get()
                response_data = preference_response.get("response")
                if not response_data or "init_point" not in response_data:
                    msg_erro = response_data.get("message") if response_data else "Erro desconhecido"
                    print(f"❌ DETALHES DO ERRO: {response_data}")
                    raise Exception(f"Falha ao gerar link: {msg_erro}")

                link_pagamento = response_data["init_point"]

                # 3. Baixa de estoque e Limpeza
                for cp in carrinho_obj.carrinhoproduto_set.all():
                    cp.produto.estoque -= cp.quantidade
                    cp.produto.save()

                del request.session["carrinho_id"]
                
                return render(request, "pagamento.html", {
                    "pedido": novo_pedido, 
                    "link_pagamento": link_pagamento
                })

        except Exception as e:
            print(f"🚨 ERRO FINAL: {e}")
            messages.error(request, f"Erro ao processar: {e}")
            return redirect("lojaapp:finalizarpedido")
# ============================================================
# ÁREA DO CLIENTE E SEGURANÇA
# ============================================================

class MeusDadosView(LoginRequiredMixin, TemplateView):
    template_name = "meus_dados.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente, _ = Cliente.objects.get_or_create(
            user=self.request.user, 
            defaults={'nome_completo': self.request.user.username}
        )
        context["enderecos"] = Endereco.objects.filter(cliente=cliente).order_by('-padrao', '-id')
        context["cliente"] = cliente
        return context

class EnderecoCreateView(LoginRequiredMixin, CreateView):
    model = Endereco
    template_name = "endereco_form.html"
    fields = ['tipo', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep', 'padrao']
    success_url = reverse_lazy('lojaapp:meusdados')
    
    def form_valid(self, form):
        form.instance.cliente = self.request.user.cliente
        messages.success(self.request, "📍 Novo endereço cadastrado!")
        return super().form_valid(form)

class EnderecoUpdateView(LoginRequiredMixin, UpdateView):
    model = Endereco
    template_name = "endereco_form.html"
    fields = ['tipo', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep', 'padrao']
    success_url = reverse_lazy('lojaapp:meusdados')

    def get_queryset(self):
        # Garante que o usuário só edite os próprios endereços
        return Endereco.objects.filter(cliente__user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "✅ Endereço atualizado com sucesso!")
        return super().form_valid(form)

class EnderecoDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        endereco = get_object_or_404(Endereco, id=pk, cliente__user=request.user)
        endereco.delete()
        messages.success(request, "🗑️ Endereço removido.")
        return redirect("lojaapp:meusdados")

class AlterarSenhaView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "alterar_senha.html", {"form": PasswordChangeForm(user=request.user)})
    
    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "🛡️ Senha atualizada com sucesso!")
            return redirect("lojaapp:meusdados")
        messages.error(request, "Erro ao atualizar senha. Verifique as regras de segurança.")
        return render(request, "alterar_senha.html", {"form": form})

# ============================================================
# LOGIN / REGISTRO / DASHBOARD
# ============================================================

class ClienteRegistroView(View):
    def get(self, request):
        return render(request, "registro.html")

    def post(self, request):
        # O .strip() remove espaços acidentais no início ou fim
        usuario = request.POST.get("username").strip() 
        email = request.POST.get("email").strip()
        senha = request.POST.get("password")
        nome_c = request.POST.get("nome_completo")

        if User.objects.filter(username=usuario).exists():
            return render(request, "registro.html", {"erro": "Este nome de usuário já existe."})

        # CRÍTICO: create_user (com _user) para criptografar a senha automaticamente
        novo_user = User.objects.create_user(usuario, email, senha)
        
        # Cria o vínculo com o modelo Cliente
        Cliente.objects.create(user=novo_user, nome_completo=nome_c)
        
        # Loga o usuário e manda para a Home
        login(request, novo_user)
        messages.success(request, f"Bem-vindo(a), {novo_user.username}!")
        return redirect("lojaapp:home")

class ClienteLoginView(View):
    def get(self, request): return render(request, "login.html")
    def post(self, request):
        user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            messages.success(request, "Login realizado com sucesso!")
            return redirect(request.GET.get("next", "lojaapp:home"))
        messages.error(request, "Usuário ou senha inválidos.")
        return render(request, "login.html")

class ClienteLogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "Você saiu da sua conta.")
        return redirect("lojaapp:home")

class AdminDashboardView(UserPassesTestMixin, TemplateView):
    template_name = "admin_dashboard.html"
    def test_func(self): return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Sum # Import local para segurança
        
        soma = Pedido_order.objects.exclude(pedido_status="Pedido Cancelado").aggregate(Sum('total'))['total__sum']
        context.update({
            "total_pedidos": Pedido_order.objects.count(),
            "faturamento_total": soma or 0,
            "total_produtos": Produto.objects.count(),
            "estoque_baixo": Produto.objects.filter(estoque__lt=5),
            "pedidos_recentes": Pedido_order.objects.all().order_by("-id")[:5]
        })
        return context

class AdminProdutoCreateView(UserPassesTestMixin, CreateView):
    model = Produto
    template_name = "admin_produto_form.html"
    fields = ['titulo', 'slug', 'categoria', 'image', 'preco_mercado', 'venda', 'estoque', 'discricao', 'garantia', 'return_devolucao']
    success_url = reverse_lazy('lojaapp:admindashboard')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        # 1. Salva o produto (foto principal)
        self.object = form.save()
        
        # 2. Pega as imagens extras do campo 'mais_imagens' que vamos criar no HTML
        fotos_extras = self.request.FILES.getlist('mais_imagens')
        
        # 3. Salva cada foto extra vinculando ao produto criado
        for foto in fotos_extras:
            ImagemProduto.objects.create(produto=self.object, imagem=foto)
            
        messages.success(self.request, "✅ Produto e galeria de fotos cadastrados com sucesso!")
        return super().form_valid(form)

# ============================================================
# VIEWS DE APOIO (HISTÓRICO E AVALIAÇÕES)
# ============================================================

class MeusPedidosView(LoginRequiredMixin, TemplateView):
    template_name = "meus_pedidos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Q 
        
        cliente, _ = Cliente.objects.get_or_create(
            user=self.request.user,
            defaults={'nome_completo': self.request.user.username}
        )
        
        # Filtro robusto para não perder nenhum pedido durante mudanças de status
        pedidos = Pedido_order.objects.filter(
            Q(carrinho__cliente=cliente) | Q(email=self.request.user.email)
        ).order_by("-id")
        
        context["pedidos"] = pedidos
        return context

class MinhasAvaliacoesView(LoginRequiredMixin, ListView):
    template_name = "minhas_avaliacoes.html"
    context_object_name = "avaliacoes"
    def get_queryset(self): 
        return Avaliacao.objects.filter(cliente__user=self.request.user).order_by("-criado_em")

class AvaliarProdutoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        produto = get_object_or_404(Produto, id=self.kwargs.get("pro_id"))
        Avaliacao.objects.update_or_create(
            produto=produto, 
            cliente=request.user.cliente, 
            defaults={'nota': request.POST.get("nota"), 'comentario': request.POST.get("comentario")}
        )
        messages.success(request, "Obrigado por avaliar este produto!")
        return redirect("lojaapp:produtodetalhe", slug=produto.slug)

class SobreView(TemplateView): template_name = "sobre.html"

class ContatoView(TemplateView):
    template_name = "contato.html"

    def post(self, request, *args, **kwargs):
        # 1. Pega os dados do formulário
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        mensagem = request.POST.get('mensagem')

        # 2. Salva no banco de dados
        MensagemContato.objects.create(
            nome=nome,
            email=email,
            mensagem=mensagem
        )

        # 3. CRIA A MENSAGEM DE CONFIRMAÇÃO
        messages.success(request, "✅ Sua mensagem foi enviada! Entraremos em contato em breve.")
        
        # 4. Limpa o formulário e volta para a página
        return redirect("lojaapp:contato")
class MeuCarrinhoView(TemplateView):
    template_name = "meu_carrinho.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrinho_id = self.request.session.get("carrinho_id", None)
        if carrinho_id:
            carrinho_obj = Carrinho.objects.filter(id=carrinho_id).first()
            context["carrinho"] = carrinho_obj
        else:
            context["carrinho"] = None
        return context
