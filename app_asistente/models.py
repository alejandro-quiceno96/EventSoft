from django.db import models

class Evento(models.Model):
    nombre = models.CharField(max_length=100)
    categorias = models.ManyToManyField('Categoria', through='EventoCategoria', related_name='eventos')

class Asistentes(models.Model):
    id = models.CharField(max_length=20, primary_key=True)  
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=45, blank=True, null=True)

    eventos = models.ManyToManyField(Evento, through='AsistenteEvento', related_name='asistentes')

class AsistenteEvento(models.Model):
    asistente = models.ForeignKey(Asistentes, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)

    fecha_hora = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=45, blank=True, null=True)
    soporte = models.BinaryField(blank=True, null=True)
    qr = models.BinaryField(blank=True, null=True)
    clave = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        unique_together = ('asistente', 'evento')  

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

class EventoCategoria(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('evento', 'categoria')  
