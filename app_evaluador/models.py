from django.db import models
from app_usuarios.models import Usuario
class Evaluadores(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='evaluador')
    
    def __str__(self):
        return f"Evaluador: {self.usuario.username} ({self.usuario.tipo_documento} {self.usuario.documento_identidad})"


class Calificaciones(models.Model):
    cal_evaluador_fk = models.ForeignKey(Evaluadores, on_delete=models.CASCADE, related_name='evaluador_calificaciones')
    cal_criterio_fk = models.ForeignKey('app_criterios.Criterios', on_delete=models.CASCADE, related_name='criterio_calificaciones')
    clas_participante_fk = models.ForeignKey('app_participante.Participantes', on_delete=models.CASCADE, related_name='participante_calificaciones')
    cal_valor = models.DecimalField(max_digits=5, decimal_places=2)
    cal_comentario = models.TextField(null=True, blank=True)
