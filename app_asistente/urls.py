
from django.urls import path
from . import views

app_name = 'app_asistente'
urlpatterns = [
    path('buscar_asistentes', views.buscar_asistentes, name="buscar_asistentes"),
    path('', views.inicio_asistente, name="inicio_asistente"),
    path('evento_asistentes/evento/<int:evento_id>/asistente/<int:asistente_id>/', views.evento_asistentes, name='evento_asistentes'),
    path('obtener_asistente/asistente/<int:asistentes_id>', views.obtener_asistente, name="modificar_asistente"),
    path('modificar_asistente/<int:asistente_id>', views.modificar_asistente, name="guardar_cambios"),
    path('cancelar_inscripcion/<int:evento_id>/asistente/<int:asistente_id>', views.cancelar_inscripcion, name = "cancelar_inscripcion" )
]