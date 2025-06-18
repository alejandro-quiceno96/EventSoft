from django.db import models
from app_usuarios.models import Usuario

class Participantes(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='participante')
    
    def __str__(self):
        return f"Participante: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"
    