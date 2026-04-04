from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=200)
    endereco_completo = models.CharField(max_length=200,null=True,blank=True)
    data_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_completo

class Categoria(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.titulo
    
class Produto(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    categoria = models.ForeignKey(Categoria,on_delete=models.CASCADE)
    image = models.ImageField(upload_to="produtos")
    preco_mercado = models.PositiveIntegerField()
    venda = models.PositiveIntegerField()
    discricao = models.TextField()
    garantia = models.CharField(max_length=300,null=True,blank=True)
    return_devolucao = models.CharField(max_length=300,null=True,blank=True)
    visualizacao = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titulo
    
class Carrinho(models.Model):
    cliente = models.ForeignKey(Cliente,on_delete=models.SET_NULL,null=True,blank=True)
    total = models.PositiveIntegerField(default=0)
    criado_em = models.DateField(auto_now_add=True)

    def __str__(self):
        return "Carrinho:" + str(self.id)

class Avaliacao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="avaliacoes")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nota = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)]) # Notas de 1 a 5
    comentario = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cliente.nome_completo} - {self.produto.titulo} ({self.nota})"
       
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

class Pedido_order(models.Model):
    carrinho = models.OneToOneField(Carrinho,on_delete=models.CASCADE)
    ordenado_por = models.CharField(max_length=200)
    endereco_envio = models.CharField(max_length=200)
    telefone = models.CharField(max_length=10)
    email = models.EmailField(null=True,blank=True)
    subtotal = models.PositiveIntegerField()
    disconto = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    pedido_status = models.CharField(max_length=50,choices=PEDIDO_STATUS)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Pedido_order:" + str(self.id)