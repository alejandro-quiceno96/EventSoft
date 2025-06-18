from django.db import models
from app_usuarios.models import Usuario

class Asistentes(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='asistente')
    
    def __str__(self):
        return f"Asistente: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"
 
