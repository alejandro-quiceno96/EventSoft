from django.db import models

class Participantes(models.Model):
    par_cedula = models.CharField(max_length=10, unique=True)
    par_nombre = models.CharField(max_length=100)
    par_correo = models.EmailField(max_length=100)
    par_telefono = models.CharField(max_length=15)
    documento = models.FileField(upload_to='documentos/', null=True, blank=True)