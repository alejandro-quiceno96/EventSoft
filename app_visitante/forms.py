from django import forms
from app_asistente.models import Asistentes, AsistenteEvento, Evento

class RegistroAsistenteForm(forms.ModelForm):
    comprobante_pago = forms.FileField(required=False, label="Comprobante de pago")

    class Meta:
        model = Asistentes
        fields = ['id', 'asi_nombre', 'asi_correo', 'asi_telefono']
