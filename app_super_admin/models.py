from django.db import models
from app_usuarios.models import Usuario  

class SuperAdministradores(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='super_admin')
    
    def __str__(self):
        return f"Super admin: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"
 