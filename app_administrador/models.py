from django.db import models
from app_usuarios.models import Usuario

class Administradores(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='administrador')
    
    def __str__(self):
        return f"Administrador: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"
    