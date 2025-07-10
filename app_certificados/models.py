from django.db import models
from app_eventos.models import Eventos

class Certificado(models.Model):
    evento_fk = models.ForeignKey(Eventos, on_delete=models.CASCADE, related_name='certificados')
    diseño = models.ImageField(upload_to='pdf/certificados/diseños/', blank=True, null=True)
    firma = models.ImageField(upload_to='pdf/certificados/firma/', blank=True, null=True)
    firma_nombre = models.CharField(max_length=100, blank=True, null=True)
    firma_cargo = models.CharField(max_length=100, blank=True, null=True)
    orientacion = models.CharField(max_length=10, choices=[('horizontal', 'Horizontal'), ('vertical', 'Vertical')], default='horizontal')

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'

    def __str__(self):
        return self.nome