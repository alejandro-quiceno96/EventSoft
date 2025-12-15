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
    eve_capacidad = models.PositiveIntegerField(null=True, blank=True)
    eve_tienecosto = models.BooleanField(default=False)
    eve_programacion = models.FileField(upload_to='pdf/programacion/', blank=True, null=True)
    eve_administrador_fk = models.ForeignKey('app_administrador.Administradores', on_delete=models.CASCADE)
    eve_informacion_tecnica = models.FileField(upload_to='pdf/info_tecnica/', blank=True, null=True)
    eve_memorias = models.URLField(max_length=200, blank=True, null=True)
    eve_habilitar_participantes = models.BooleanField(default=True)
    eve_habilitar_evaluadores = models.BooleanField(default=True)


class EventosCategorias(models.Model):
    eve_cat_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    eve_cat_categoria_fk = models.ForeignKey('app_categorias.Categorias', on_delete=models.CASCADE)

class AsistentesEventos(models.Model):
    asi_eve_asistente_fk = models.ForeignKey('app_asistente.Asistentes', on_delete=models.CASCADE)
    asi_eve_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    asi_eve_fecha_hora = models.DateTimeField(auto_now_add=True)
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
    par_eve_calificacion_final = models.FloatField(null=True, blank=True)
    par_eve_proyecto = models.ForeignKey('Proyecto', on_delete=models.CASCADE, null=True, blank=True)
    habilitado = models.BooleanField(default=True)
    
class EvaluadoresEventos(models.Model):
    eva_eve_evaluador_fk = models.ForeignKey('app_evaluador.Evaluadores', on_delete=models.CASCADE)
    eva_eve_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    eva_eve_fecha_hora = models.DateTimeField(null=True, blank=True)
    eva_eve_areas_interes = models.TextField(max_length=400, null=True, blank=True)
    eva_eve_documentos = models.FileField(upload_to='pdf/soporte_evaluador/',null=True, blank=True)
    eva_estado = models.CharField(max_length=45, null=True, blank=True)
    eva_eve_qr = models.FileField(upload_to='pdf/qr_evaluador/',null=True, blank=True)
    eva_clave_acceso = models.CharField(max_length=45, null=True, blank=True)
    habilitado = models.BooleanField(default=True)
    criterios_modificables = models.BooleanField(default=False, null=True, blank=True)
    
class Proyecto(models.Model):
    pro_evento_fk = models.ForeignKey('Eventos', on_delete=models.CASCADE)
    pro_codigo = models.CharField(max_length=8)
    pro_nombre = models.CharField(max_length=100)
    pro_descripcion = models.TextField(max_length=400)
    pro_documentos = models.FileField(upload_to='pdf/proyectos/')
    pro_fecha_hora = models.DateTimeField(auto_now_add=True)
    pro_estado = models.CharField(max_length=45)
    pro_calificación_final = models.FloatField(null=True, blank=True)