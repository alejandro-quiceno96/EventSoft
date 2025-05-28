from django.urls import path
from . import views

app_name = 'app_evaluador'


urlpatterns = [
   path('inicio_sesion_evaluador', views.inicio_sesion_evaluador, name='inicio_sesion_evaluador'),
   path('principal/<int:evaluador_id>/', views.principal_evaluador, name='principal_evaluador'),
    path('ver_participantes/<int:evento_id>/', views.ver_participantes, name='ver_participantes'),
   path('evaluador/evaluar_participante/<int:evento_id>/<int:participante_id>/<int:evaluador_id>/', views.evaluar_participante, name='evaluar_participante'),

    
]   



    
    