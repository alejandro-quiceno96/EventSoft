from django.urls import path
from . import views

app_name = 'app_evaluador'


urlpatterns = [
    path('', views.inicio_sesion, name='inicio_sesion'),
    path('inicio/', views.vista_inicio, name='inicio'),
    path('evaluacion/<int:participante_id>/', views.evaluacion_participante, name='evaluacion_participante'),
    path('criterios/', views.criterios_evaluacion, name='criterios'),
    path('participantes/<int:evento_id>/', views.participantes_por_evento, name='participantes'),
    path('guardar_evaluacion/', views.guardar_evaluacion, name='guardar_evaluacion'),
   
]



    
    