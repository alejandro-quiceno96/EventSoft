from django.db import models

class Eventos(models.Model):
    
    eve_nombre = models.CharField(max_length=100)
    eve_descripcion = models.TextField(max_length=400)
    eve_ciudad = models.CharField(max_length=100)
    eve_lugar = models.CharField(max_length=100)
    eve_fecha_inicio = models.DateField()
    eve_fecha_fin = models.DateField()
    eve_estado = models.CharField(max_length=100)
    eve_imagen = models.ImageField(upload_to='image/')
    eve_capacidad = models.IntegerField()
    eve_tienecosto = models.BooleanField(default=False)
    eve_programacion = models.FileField(upload_to='pdf/programacion/')
    eve_administrador_fk = models.ForeignKey('app_administrador.Administradores', on_delete=models.CASCADE)

class EventosCategorias(models.Model):
    eve_cat_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    eve_cat_categoria_fk = models.ForeignKey('app_categorias.Categorias', on_delete=models.CASCADE)

class AsistentesEventos(models.Model):
    asi_eve_asistente_fk = models.ForeignKey('app_asistente.Asistentes', on_delete=models.CASCADE)
    asi_eve_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    asi_eve_fecha_hora = models.DateTimeField()
    asi_eve_estado = models.CharField(max_length=45)
    asi_eve_soporte = models.FileField(upload_to='pdf/comprobantes/')
    asi_eve_qr = models.FileField(upload_to='pdf/qr_asistentes/')
    asi_eve_clave = models.CharField(max_length=45)
    
class ParticipantesEventos(models.Model):
    par_eve_participante_fk = models.ForeignKey('app_participante.Participantes', on_delete=models.CASCADE)
    par_eve_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    par_eve_fecha_hora = models.DateTimeField()
    par_eve_documentos = models.FileField(upload_to='pdf/proyectos/')
    par_eve_estado = models.CharField(max_length=45)
    par_eve_qr = models.FileField(upload_to='pdf/qr_participante/')
    par_eve_clave = models.CharField(max_length=45)