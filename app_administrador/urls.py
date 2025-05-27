from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'administrador'

urlpatterns=[
    path('', views.inicio, name='index_administrador' ),
    path('crear_evento/', views.crear_evento, name='crear_evento' ),
    path('get_categorias/<int:area_id>', views.get_categorias, name='get_categorias' ),
    path('event/<int:evento_id>', views.obtener_evento, name='evento_detalle'),
    path('eliminar/<int:evento_id>', views.eliminar_evento, name='eliminar_evento'),
    path('inicio_sesion/', views.inicio_sesion_administrador, name='inicio_sesion_administrador'),
    path('editar_evento/<int:evento_id>', views.editar_evento, name='editar_evento'),
    
    path('evento/<int:evento_id>/participantes/', views.ver_participantes, name='ver_participantes'),
    path('actualizar_estado_participante/<int:participante_id>/<str:nuevo_estado>/', views.actualizar_estado, name='actualizar_estado'),
    
    path('evento/<int:evento_id>/asistentes/', views.ver_asistentes, name='ver_asistentes'),
    path('actualizar_estado_asistente/<int:asistente_id>/<str:nuevo_estado>/', views.actualizar_estado_asistente, name='actualizar_estado_asistente'),
    
    #criterios de evaluacion
    path('criterios_evaluacion/<int:evento_id>', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('modificar_criterio/<int:criterio_id>', views.modificar_criterio, name='modificar_criterio'),
    path('eliminar_criterio/<int:criterio_id>', views.eliminar_criterio, name='eliminar_criterio'),

    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

