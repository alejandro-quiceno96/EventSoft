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
    
    path('evento/<int:evento_id>/participantes/', views.ver_participantes, name='ver_participantes'),
    path('actualizar_estado_participante/<int:participante_id>/<str:nuevo_estado>/', views.actualizar_estado, name='actualizar_estado'),
    
    path('evento/<int:evento_id>/asistentes/', views.ver_asistentes, name='ver_asistentes'),
    path('actualizar_estado_asistente/<int:asistente_id>/<str:nuevo_estado>/', views.actualizar_estado_asistente, name='actualizar_estado_asistente'),
    
    path('evento/<int:evento_id>/evaluadores/', views.ver_evaluadores, name='ver_evaluadores'),
    path('evaluador/<int:evaluador_id>/estado/<str:nuevo_estado>/', views.actualizar_estado_evaluador, name='actualizar_estado_evaluador'),
    

    #criterios de evaluacion
    path('criterios_evaluacion/<int:evento_id>', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('modificar_criterio/<int:criterio_id>', views.modificar_criterio, name='modificar_criterio'),
    path('eliminar_criterio/<int:criterio_id>', views.eliminar_criterio, name='eliminar_criterio'),
    
    #calificaciones
    path('tabla_calificaciones/<int:evento_id>', views.tabla_calificaciones, name='tabla_calificaciones'),
    path('descargar_raking/<int:evento_id>', views.descargar_ranking_pdf, name = "descargar_ranking_pdf" ),
    path('evento/<int:evento_id>/participante/<int:participante_id>/detalles/', views.detalles_calificaciones, name='detalle_calificaciones'),
    path('detalle_calificacion/evaluador/<int:evaluador_id>/partcipante/<int:participante_id>/evento/<int:evento_id>/', views.detalle_calificacion, name= "detalle_calificacion"),

    path('evento/<int:evento_id>/enviar_certificados/', views.enviar_certificados, name='enviar_certificados'),
    path('evento/<int:evento_id>/participantes/enviar_certificados/', views.enviar_certificados_participantes, name='enviar_certificados_participantes'),
    path('evento/<int:evento_id>/evaluadores/enviar_certificados/', views.enviar_certificados_evaluadores, name='enviar_certificados_evaluadores'),
 
    path('evento/<int:evento_id>/notificar/', views.enviar_notificacion_asistentes, name='enviar_notificacion'),


    path('evento/<int:evento_id>/enviar_notificacion/', views.notificacion_personal, name='enviar'),
    
    path('evento/<int:evento_id>/notificar-participante/', views.enviar_notificacion_participante, name='enviar_participantes'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

