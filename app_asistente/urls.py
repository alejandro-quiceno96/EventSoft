
from django.urls import path
from . import views

app_name = 'app_asistente'
urlpatterns = [
    path('', views.inicio_asistente, name="inicio_asistente"),
    path('evento_asistentes/evento/<int:evento_id>/asistente/<int:asistente_id>/', views.evento_asistentes, name='evento_asistentes'),
    path('cancelar_inscripcion/<int:evento_id>/asistente/<int:asistente_id>', views.cancelar_inscripcion, name = "cancelar_inscripcion" ),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
]