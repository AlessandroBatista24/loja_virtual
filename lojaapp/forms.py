from django import forms
from .models import Pedido_order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Pedido_order
        fields = ["ordenado_por", "endereco", "numero", "bairro", "cidade", "estado", "cep", "telefone", "email"]
        widgets = {
            'ordenado_por': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
