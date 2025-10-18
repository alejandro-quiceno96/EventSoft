
from django.urls import path
from . import views

app_name = 'app_asistente'
urlpatterns = [
    path('', views.inicio_asistente, name="inicio_asistente"),
    path('evento_asistentes/evento/<int:evento_id>/asistente/<int:asistente_id>/', views.evento_asistentes, name='evento_asistentes'),
    path('cancelar_inscripcion/<int:evento_id>/asistente/<int:asistente_id>', views.cancelar_inscripcion, name = "cancelar_inscripcion" ),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('inscripciones/', views.inicio_asistente, name='asistente_inscripciones'),


    
    path(
        'programacion/<int:evento_id>/',
        views.ver_programacion_evento,
        name='ver_programacion_evento'
    ),
    path(
        'programacion/<int:evento_id>/descargar_pdf/',
        views.descargar_programacion_pdf,
        name='descargar_programacion_pdf'
    ),
    path(
        'enviar-certificados/<int:evento_id>/',
        views.enviar_certificado_asistentes,
        name='enviar_certificado_asistentes'
    ),
        path('descargar_memorias/<int:evento_id>/', views.descargar_memorias, name='descargar_memorias'),

]