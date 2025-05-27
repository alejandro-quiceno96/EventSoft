from django.urls import path
from . import views

app_name = 'app_participante'

urlpatterns = [
    path('Buscar_eventos_pre/', views.buscar_participantes, name='buscar_participantes'),
    path('ver_info_participante/', views.info_participantes_eventos, name='ver_info_participante'),
    path('cancelar_inscripcion/', views.cancelar_inscripcion, name='cancelar_inscripcion'),
    path('modificar_inscripcion/', views.modificar_inscripcion, name='modificar_inscripcion'),
   
    path('api/evento/<int:evento_id>/detalle/', views.api_detalle_evento, name='api_detalle_evento'),

]

