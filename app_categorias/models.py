from django.db import models

class Categorias(models.Model):
    cat_nombre = models.CharField(max_length=100)
    cat_descripcion = models.TextField(max_length=400)
    cat_area_fk = models.ForeignKey('app_areas.Areas', on_delete=models.CASCADE)
