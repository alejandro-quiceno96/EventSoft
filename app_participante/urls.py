from django.urls import path
from . import views

app_name = 'app_participante'

urlpatterns = [
    path('Buscar_eventos_pre/', views.buscar_participantes, name='buscar_participantes'),
    path('ver_info_participante/', views.info_participantes_eventos, name='ver_info_participante'),
    path("event/<int:evento_id>/participante/<int:participante_id>", views.evento_detalle_participante, name= "detalle_evento"),
    path('generar_pdf_criterios/<int:evento_id>', views.generar_pdf_criterios, name= "generar_pdf_criterios"),
    

]

