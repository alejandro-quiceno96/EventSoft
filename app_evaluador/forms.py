# forms.py

from django import forms
from .models import Evaluadores

class EvaluadorForm(forms.ModelForm):
    class Meta:
        model = Evaluadores
        fields = ['eva_nombre', 'eva_correo', 'eva_telefono']
        widgets = {
            'eva_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'eva_correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'eva_telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
