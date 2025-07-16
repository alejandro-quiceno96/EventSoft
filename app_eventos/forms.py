from django import forms
from .models import EstadosInscripcionesEvento

class EstadosInscripcionesEventoForm(forms.ModelForm):
    class Meta:
        model = EstadosInscripcionesEvento
        fields = ['permitir_participantes', 'permitir_evaluadores']
