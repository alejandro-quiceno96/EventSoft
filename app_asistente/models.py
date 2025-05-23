from django.db import models

class Asistentes(models.Model):
    asi_cedula = models.CharField(max_length=10, unique=True)
    asi_nombre = models.CharField(max_length=100)
    asi_correo = models.EmailField(max_length=100)
    asi_telefono = models.CharField(max_length=15)
