from django.db import models

class Criterios(models.Model):
    cri_descripcion = models.CharField(max_length=1000)
    cri_peso = models.DecimalField(max_digits=5, decimal_places=2)
    cri_evento_fk = models.ForeignKey('app_eventos.Eventos', on_delete=models.CASCADE, related_name='eventos_criterios')

    def __str__(self):
        return self.cri_descripcion
