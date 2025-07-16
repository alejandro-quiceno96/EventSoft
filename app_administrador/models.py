from django.db import models
from app_usuarios.models import Usuario

class Administradores(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='administrador')
    num_eventos = models.IntegerField(default=0 ,blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    tiempo_limite = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    clave_acceso = models.CharField(max_length=8, blank=True, null=True)
    
    def __str__(self):
        return f"Administrador: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"
    