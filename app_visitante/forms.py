from django import forms
from django.contrib.auth.forms import UserCreationForm
from app_usuarios.models import Usuario

TIPOS_DOCUMENTO = [
    ('CC', 'Cédula de ciudadanía'),
    ('TI', 'Tarjeta de identidad'),
    ('CE', 'Cédula de extranjería'),
    ('PA', 'Pasaporte'),
]

class RegistroUsuarioForm(UserCreationForm):
    tipo_documento = forms.ChoiceField(choices=TIPOS_DOCUMENTO, required=True)
    documento_identidad = forms.CharField(max_length=20, required=True)
    first_name = forms.CharField(label='Primer Nombre')
    last_name = forms.CharField(label='Primer Apellido')
    segundo_nombre = forms.CharField(required=False)
    segundo_apellido = forms.CharField(required=False)
    telefono = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Usuario
        fields = [
            'username', 'tipo_documento', 'documento_identidad', 'first_name', 'segundo_nombre',
            'last_name', 'segundo_apellido', 'telefono', 'email', 'fecha_nacimiento',
            'password1', 'password2'
        ]
