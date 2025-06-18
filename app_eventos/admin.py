from django.contrib import admin
from .models import Eventos, EventosCategorias, EvaluadoresEventos, ParticipantesEventos, AsistentesEventos

admin.site.register(Eventos)
admin.site.register(EventosCategorias)
admin.site.register(EvaluadoresEventos)
admin.site.register(ParticipantesEventos)
admin.site.register(AsistentesEventos)
