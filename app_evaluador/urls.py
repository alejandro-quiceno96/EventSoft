from django.urls import path
from . import views

app_name = 'app_evaluador'

urlpatterns = [
    path('inicio_sesion_evaluador', views.inicio_sesion_evaluador, name='inicio_sesion_evaluador'),
    path('principal/<int:evaluador_id>/', views.principal_evaluador, name='principal_evaluador'),
    path('ver_participantes/<int:evento_id>/', views.ver_participantes, name='ver_participantes'),
    
    # ✅ Parámetros con nombres correctos
    path('evaluar_participante/<int:evento_id>/<int:participante_id>/<int:evaluador_id>/', views.evaluar_participante, name='evaluar_participante'),
    path('evento/<int:evento_id>/criterios/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('criterios/<int:evento_id>/', views.criterios_evaluacion, name='criterios_evento'),
    path('calificaciones/<int:evento_id>/<int:participante_id>/<int:evaluador_id>/', 
     views.obtener_calificaciones, 
     name='api_calificaciones'),
    path('buscar evaluador/', views.buscar_evaluador, name='buscar_evaluador'),
   path('informacion/', views.informacion_evaluador, name='informacion_evaluador'),
    
    # APIs para obtener y modificar datos del evaluador
    path('api/obtener/<str:cedula>/', views.obtener_datos_evaluador, name='obtener_datos_evaluador'),
    
    path('editar/<int:evaluador_id>/', views.editar_evaluador, name='editar_evaluador'),

    # URL para obtener datos del evaluador (si la necesitas)
    path('datos/<str:cedula>/', views.obtener_datos_evaluador, name='obtener_datos_evaluador'),
    

    # Detalles del evento para evaluador# app_evaluador/urls.py
# urls.py
path('evaluador/evaluador/<str:evaluador_cedula>/evento/<int:evento_id>/', views.detalle_evento_evaluador, name='detalle_evento_evaluador'),

    
    # Reportes
    path('reporte/<str:cedula>/', views.generar_reporte_evaluador, name='generar_reporte_evaluador'),
    path('evaluador/evento/<int:evento_id>/evaluador/<str:evaluador_cedula>/', views.detalle_evento_json, name='detalle_evento_json'),

    # Participantes por evaluar
    path('participantes/<str:evaluador_cedula>/<int:evento_id>/', views.participantes_por_evaluar, name='participantes_por_evaluar'),
    # Detalle del evento  para evaluador
    path('detalle-evento/html/<int:cedula>/<int:evento_id>/', views.detalle_evento, name='detalle_evento_evaluador'),
    path('inicio_evaluador/', views.inicio_evaluador, name='inicio_evaluador'),


    #cancelar preinscripción
    path('cancelar-preinscripcion/<int:evento_id>/<str:cedula>/', views.cancelar_preinscripcion, name='cancelar_preinscripcion'),
   




]
