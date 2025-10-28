from django.urls import path
from . import views

app_name = 'app_participante'

urlpatterns = [
    path('ver_info_participante/', views.ver_info_participantes_eventos, name='ver_info_participante'),
    path("event/<int:evento_id>/participante/<int:participante_id>", views.evento_detalle_participante, name= "detalle_evento"),
    path('generar_pdf_criterios/<int:evento_id>', views.generar_pdf_criterios, name= "generar_pdf_criterios"),
    path("obtener_datos_participante/<int:participante_id>/evento/<int:evento_id>", views.obtener_datos_participante, name="obtener_datos_participante"),
    path('modificar_inscripcion/<int:evento_id>/participante/<int:participante_id>/', views.modificar_inscripcion, name='modificar_inscripcion'),
    path('cancelar_inscripcion/<int:evento_id>/participante/<int:participante_id>/', views.cancelar_inscripcion, name = "cancelar_inscripcion" ),
    path('descargar_comentarios/<int:evento_id>/', views.generar_pdf_comentarios_participante, name='descargar_comentarios'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
]

