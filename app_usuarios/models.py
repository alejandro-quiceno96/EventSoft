from django.db import models
from django.contrib.auth.models import AbstractUser

TIPO_DOCUMENTO_CHOICES = [
    ('CC', 'Cédula de Ciudadanía'),
    ('TI', 'Tarjeta de Identidad'),
    ('CE', 'Cédula de Extranjería'),
    ('PA', 'Pasaporte'),
    ('RC', 'Registro Civil'),
    ('PEP', 'Permiso Especial de Permanencia'),
]

class Usuario(AbstractUser):
    segundo_nombre = models.CharField(
        max_length=100,
        verbose_name='Segundo Nombre',
        blank=True,
        null=True
    )
    segundo_apellido = models.CharField(
        max_length=100,
        verbose_name='Segundo Apellido',
        blank=True,
        null=True
    )
    
    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name='Tipo de Documento',
        blank=True,
        null=True
    )
    documento_identidad = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Documento de Identidad',
        blank=True,
        null=True
    )
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de Nacimiento',
        blank=True,
        null=True
    )
    telefono = models.CharField(
        max_length=15,
        verbose_name='Telefono',
        blank=True,
        null=True
    )
    
    
    
    def __str__(self):
        return self.username
