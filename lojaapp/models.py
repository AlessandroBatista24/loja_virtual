from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg 

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=200)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    data_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_completo

class Endereco(models.Model):
    TIPO_CHOICES = (('Casa', 'Casa'), ('Trabalho', 'Trabalho'), ('Outro', 'Outro'))
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="meus_enderecos")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='Casa')
    rua = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
    padrao = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.padrao:
            Endereco.objects.filter(cliente=self.cliente, padrao=True).update(padrao=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.rua}, {self.numero}"

class Categoria(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.titulo
    
class Produto(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="produtos")
    preco_mercado = models.PositiveIntegerField(null=True, blank=True)
    venda = models.PositiveIntegerField(null=True, blank=True) # Permitimos nulo para o Python calcular
    discricao = models.TextField()
    garantia = models.CharField(max_length=300, null=True, blank=True)
    return_devolucao = models.CharField(max_length=300, null=True, blank=True)
    visualizacao = models.PositiveIntegerField(default=0)
    estoque = models.PositiveIntegerField(default=0)
    
    # Campos Financeiros
    preco_custo = models.PositiveIntegerField(default=0)
    imposto_percentual = models.PositiveIntegerField(default=0, help_text="Ex: 6 para 6%")
    taxa_venda_percentual = models.PositiveIntegerField(default=0, help_text="Taxa cartão/marketplace")
    custo_fixo_unidade = models.PositiveIntegerField(default=0, help_text="Custo de embalagem, frete fixo, etc.")
    margem_desejada = models.PositiveIntegerField(default=20, help_text="Quanto você quer ganhar limpo (%)")

    def media_avaliacao(self):
        media = self.avaliacoes.aggregate(Avg('nota'))['nota__avg']
        return round(media) if media else 0

    def save(self, *args, **kwargs):
        # Lógica de cálculo de Preço de Venda (Markup)
        taxas_totais = self.imposto_percentual + self.taxa_venda_percentual + self.margem_desejada
        
        if taxas_totais < 100:
            divisor = (100 - taxas_totais) / 100
            # Preço = (Custos Fixos + Custo Produto) / Margem Restante
            calculo = (self.preco_custo + self.custo_fixo_unidade) / divisor
            self.venda = round(calculo)
        
        # Garante que o preço de mercado não fique vazio
        if not self.preco_mercado or self.preco_mercado < self.venda:
            self.preco_mercado = round(self.venda * 1.2) # Sugere 20% acima do preço de venda

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Avaliacao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="avaliacoes")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nota = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)]) 
    comentario = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cliente.nome_completo} - {self.produto.titulo} ({self.nota})"

class Cupom(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    valor_desconto = models.PositiveIntegerField(help_text="Valor fixo de desconto em R$")
    ativo = models.BooleanField(default=True)
    minimo_pedido = models.PositiveIntegerField(default=0, help_text="Valor mínimo do carrinho para usar")

    def __str__(self):
        return f"{self.codigo} (R$ {self.valor_desconto})"
    
class Carrinho(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.PositiveIntegerField(default=0)
    criado_em = models.DateField(auto_now_add=True)

    def __str__(self):
        return "Carrinho:" + str(self.id)
       
class CarrinhoProduto(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField()

    def __str__(self):
        return f"Carrinho: {self.carrinho.id} - Item: {self.produto.titulo}"
    
PEDIDO_STATUS =(
    ("Pedido Recebido","Pedido Recebido"),
    ("Pedido Processando","Pedido Processando"),
    ("Pedido Caminho","Pedido Caminho"),
    ("Pedido Finalizado","Pedido Finalizado"),
    ("Pedido Cancelado","Pedido Cancelado"),
)

# --- OPÇÕES DE STATUS E PAGAMENTO (FORA DA CLASSE) ---

PEDIDO_STATUS = (
    ("Pedido Recebido", "Pedido Recebido"),
    ("Pedido Processando", "Pedido Processando"),
    ("Pedido Caminho", "Pedido Caminho"),
    ("Pedido Finalizado", "Pedido Finalizado"),
    ("Pedido Cancelado", "Pedido Cancelado"),
)

METODO_PAGAMENTO = (
    ("Pix", "Pix"),
    ("Cartao", "Cartão de Crédito"),
    ("Boleto", "Boleto Bancário"),
)

PAGAMENTO_STATUS = (
    ("Pendente", "Pendente"),
    ("Pago", "Pago"),
    ("Cancelado", "Cancelado"),
)

# --- MODELO DE PEDIDO ---

class Pedido_order(models.Model):
    carrinho = models.OneToOneField(Carrinho, on_delete=models.CASCADE)
    ordenado_por = models.CharField(max_length=200)
    endereco = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2) 
    cep = models.CharField(max_length=10)
    telefone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    
    # Valores Financeiros
    subtotal = models.PositiveIntegerField()
    disconto = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    
    # Status do Pedido (Logística)
    pedido_status = models.CharField(max_length=50, choices=PEDIDO_STATUS, default="Pedido Recebido")
    criado_em = models.DateTimeField(auto_now_add=True)

    # Controle de Pagamento
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO, default="Pix")
    pagamento_status = models.CharField(max_length=20, choices=PAGAMENTO_STATUS, default="Pendente")
    pagamento_confirmado = models.BooleanField(default=False)
    id_transacao = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Pedido: {self.id} - {self.ordenado_por}"


class PedidoRecebido(Pedido_order):
    class Meta:
        proxy = True
        verbose_name = 'Pedido - 1. Novo'
        verbose_name_plural = 'Pedidos - 1. Novos (Recebidos)'

class PedidoProcessando(Pedido_order):
    class Meta:
        proxy = True
        verbose_name = 'Pedido - 2. Em Preparo'
        verbose_name_plural = 'Pedidos - 2. Processando'

class PedidoCaminho(Pedido_order):
    class Meta:
        proxy = True
        verbose_name = 'Pedido - 3. Enviado'
        verbose_name_plural = 'Pedidos - 3. A Caminho'

class PedidoFinalizado(Pedido_order):
    class Meta:
        proxy = True
        verbose_name = 'Pedido - 4. Concluído'
        verbose_name_plural = 'Pedidos - 4. Finalizados'

    def __str__(self):
        return f"Pedido: {self.id} - {self.ordenado_por}"
    
class ImagemProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="imagens")
    imagem = models.ImageField(upload_to="produtos/galeria")
    
class Banner(models.Model):
    titulo = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to="banners/")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class MensagemContato(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensagem de {self.nome}"

