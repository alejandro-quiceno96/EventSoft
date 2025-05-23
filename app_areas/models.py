from django.db import models

class Areas(models.Model):
    are_nombre = models.CharField(max_length=100)
    are_descripcion = models.TextField(max_length=400)
