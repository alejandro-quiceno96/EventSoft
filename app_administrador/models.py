from django.db import models

class Administradores(models.Model):
    adm_cedula = models.CharField(max_length=10)
    adm_nombre = models.CharField(max_length=100)
    adm_correo = models.EmailField(max_length=100)
    adm_telefono = models.CharField(max_length=15)