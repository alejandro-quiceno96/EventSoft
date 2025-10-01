from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'administrador'

urlpatterns=[
    path('', views.inicio, name='index_administrador' ),
    path('crear_evento/', views.crear_evento, name='crear_evento' ),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil' ),
    path('get_categorias/<int:area_id>', views.get_categorias, name='get_categorias' ),
    path('event/<int:evento_id>', views.obtener_evento, name='evento_detalle'),
    path('eliminar/<int:evento_id>', views.eliminar_evento, name='eliminar_evento'),
    path('editar_evento/<int:evento_id>', views.editar_evento, name='editar_evento'),
    
    path('evento/<int:evento_id>/participantes/', views.ver_proyectos, name='ver_participantes'),
    path('actualizar_estado_proyecto/<int:proyecto_id>/<str:nuevo_estado>/', views.actualizar_estado_proyecto, name='actualizar_estado'),

    path('evento/<int:evento_id>/asistentes/', views.ver_asistentes, name='ver_asistentes'),
    path('actualizar_estado_asistente/<int:asistente_id>/<str:nuevo_estado>/', views.actualizar_estado_asistente, name='actualizar_estado_asistente'),
    
    path('evento/<int:evento_id>/evaluadores/', views.ver_evaluadores, name='ver_evaluadores'),
    path('evaluador/<int:evaluador_id>/estado/<str:nuevo_estado>/', views.actualizar_estado_evaluador, name='actualizar_estado_evaluador'),
    
    #Asignar evaluadores
    path('evaluadores/listar/<int:evento_id>/<int:proyecto_id>/', views.listar_evaluadores_ajax, name='listar_evaluadores'),
    path('evaluador/asignar/<int:evento_id>/<int:proyecto_id>/<int:evaluador_id>/', views.asignar_evaluador_ajax, name='asignar_evaluador'),
    path('evaluador/designar/<int:evento_id>/<int:proyecto_id>/<int:evaluador_id>/', views.designar_evaluador_ajax, name='designar_evaluador'),

    #criterios de evaluacion
    path('criterios_evaluacion/<int:evento_id>', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('modificar_criterio/<int:criterio_id>', views.modificar_criterio, name='modificar_criterio'),
    path('eliminar_criterio/<int:criterio_id>', views.eliminar_criterio, name='eliminar_criterio'),
    
    #calificaciones
    path('tabla_calificaciones/<int:evento_id>', views.tabla_calificaciones, name='tabla_calificaciones'),
    path('descargar_raking/<int:evento_id>', views.descargar_ranking_pdf, name = "descargar_ranking_pdf" ),
    path('evento/<int:evento_id>/proyecto/<int:proyecto_id>/detalles/', views.detalles_calificaciones, name='detalle_calificaciones'),
    path('detalle_calificacion/evaluador/<int:evaluador_id>/proyecto/<int:proyecto_id>/evento/<int:evento_id>/', views.detalle_calificacion, name= "detalle_calificacion"),

    #correos
    path('enviar_correo/<int:evento_id>', views.enviar_correo, name='enviar_correo'),
    path('enviar_certificado_participantes/<int:evento_id>/', views.enviar_certificado_participantes, name='enviar_certificado_participantes'),
    path('enviar_certificado_asistentes/<int:evento_id>/', views.enviar_certificado_asistentes, name='enviar_certificado_asistentes'),
    path('enviar_certificado_evaluadores/<int:evento_id>/', views.enviar_certificado_evaluadores, name='enviar_certificado_evaluadores'),
    path('enviar_certificado_primer_lugar/<int:evento_id>/<int:proyecto_id>/', views.enviar_certificado_reconocimiento, name='enviar_certificado_reconocimiento'),


    #memorias
    path('guardar-memorias/', views.guardar_memorias, name='guardar_memorias'),
    
    #certificados
    path('configuracion_certificados/<int:evento_id>/', views.configuracion_certificados, name='configuracion_certificados'),
    path('certificados/<int:evento_id>/descargar/', views.descargar_certificado_pdf, name='descargar_certificado_pdf'),
    path('certificados/<int:evento_id>/modificar/', views.modificar_certificados, name='modificar_certificados'),

    # habilitar y desabilitar
    path("configurar-inscripcion/<int:evento_id>", views.config_inscripcion, name="configurar_inscripcion"),


    path('evento/subir-info-tecnica/<int:evento_id>/', views.subir_info_tecnica, name='subir_info_tecnica'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

