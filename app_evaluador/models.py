from django.db import models

class Evaluadores(models.Model):
    eva_cedula = models.CharField(max_length=10, unique=True)
    eva_nombre = models.CharField(max_length=100)
    eva_correo = models.EmailField(max_length=100)
    eva_telefono = models.CharField(max_length=15)

    def __str__(self):
        return self.eva_nombre


class Calificaciones(models.Model):
    cal_evaluador_fk = models.ForeignKey(Evaluadores, on_delete=models.CASCADE, related_name='evaluador_calificaciones')
    cal_criterio_fk = models.ForeignKey('app_criterios.Criterios', on_delete=models.CASCADE, related_name='criterio_calificaciones')
    clas_participante_fk = models.ForeignKey('app_participante.Participantes', on_delete=models.CASCADE, related_name='participante_calificaciones')
    cal_valor = models.DecimalField(max_digits=5, decimal_places=2)
    cal_comentario = models.TextField(null=True, blank=True)
