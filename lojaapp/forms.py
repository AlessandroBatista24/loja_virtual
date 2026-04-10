from django import forms
from .models import Pedido_order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Pedido_order
        fields = ["ordenado_por", "endereco_envio", "telefone", "email"]
        widgets = {
            'ordenado_por': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco_envio': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
