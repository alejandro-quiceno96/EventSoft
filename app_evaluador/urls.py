from django.urls import path
from . import views

app_name = 'app_evaluador'

urlpatterns = [
    path('principal/', views.principal_evaluador, name='principal_evaluador'),
    path('ver_participantes/<int:evento_id>/', views.ver_participantes, name='ver_participantes'),
    
    # ✅ Parámetros con nombres correctos
    path('evaluar_participante/<int:evento_id>/<int:proyecto_id>/<int:evaluador_id>/', views.evaluar_participante, name='evaluar_participante'),
    path('evento/<int:evento_id>/criterios/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('criterios/<int:evento_id>/', views.criterios_evaluacion, name='criterios_evento'),
    # urls.py de app_evaluador
    path('api/calificaciones/<int:evento_id>/<int:proyecto_id>/<int:evaluador_id>/',
    views.api_calificaciones,
    name='api_calificaciones'),

    
    # Reportes
    path('reporte/<str:cedula>/', views.generar_reporte_evaluador, name='generar_reporte_evaluador'),

    # Participantes por evaluar
    path('participantes/<str:evaluador_cedula>/<int:evento_id>/', views.participantes_por_evaluar, name='participantes_por_evaluar'),
    # Detalle del evento  para evaluador
    path('detalle-evento/html/<int:cedula>/<int:evento_id>/', views.detalle_evento, name='detalle_evento_evaluador'),
    path('inicio_evaluador/', views.inicio_evaluador, name='inicio_evaluador'),


    #cancelar preinscripción
    path('cancelar-inscripcion/<int:evento_id>/<int:evaluador_id>/', views.cancelar_inscripcion, name='cancelar_inscripcion'),
    path('evento/<int:pk>/subir-info-tecnica/', views.subir_info_tecnica, name='subir_info_tecnica'),

    path('evento/<int:evento_id>/criterios_modificables/', views.modificar_criterios_evaluacion, name='crud_criterios_evento'),
    
    #modificar inscripcion
    path('obtener_datos_preinscripcion/<int:evento_id>/<int:evaluador_id>/', views.obtener_datos_preinscripcion, name='obtener_datos_preinscripcion'),
    path('modificar_preinscripcion/<int:evento_id>/<int:evaluador_id>/', views.modificar_preinscripcion, name='modificar_preinscripcion'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
]
