from django.urls import path
from . import views
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase

urlpatterns = [
    path('', views.inicio_visitante, name='inicio_visitante'),
    path('evento/<int:evento_id>/', views.detalle_evento, name='detalle_evento'),
    path('participante/<int:evento_id>/', views.preinscripcion_participante, name='preinscripcion_participante'),
    path('asistente/<int:evento_id>/', views.preinscripcion_asistente, name='preinscripcion_asistente'),
    path('modificar_participante/', views.modificar_participante, name='modificar_participante'),
    path('submit_preinscripcion/', views.submit_preinscripcion_participante, name='submit_preinscripcion_participante'),
    path('registro/<int:evento_id>/', views.registrar_asistente, name='registrar_asistente'),
    path('inicio_evaluado/', views.inicio_evaluador, name='inicio_sesion_evaluador'),
]
