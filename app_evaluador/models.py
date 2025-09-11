from django.db import models
from app_usuarios.models import Usuario
from app_eventos.models import Proyecto
class Evaluadores(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='evaluador')
    
    def __str__(self):
        return f"Evaluador: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"


class Calificaciones(models.Model):
    cal_evaluador_fk = models.ForeignKey(Evaluadores, on_delete=models.CASCADE, related_name='evaluador_calificaciones')
    cal_criterio_fk = models.ForeignKey('app_criterios.Criterios', on_delete=models.CASCADE, related_name='criterio_calificaciones')
    clas_proyecto_fk = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='proyecto_calificaciones', blank=True, null=True)
    cal_valor = models.DecimalField(max_digits=5, decimal_places=2)
    cal_comentario = models.TextField(null=True, blank=True)

class EvaluadorProyecto(models.Model):
    eva_pro_evaluador_fk = models.ForeignKey(Evaluadores, on_delete=models.CASCADE, related_name='evaluador')
    eva_pro_proyecto_fk = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='proyecto')