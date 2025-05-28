from django.urls import path
from . import views

app_name = 'app_evaluador'

urlpatterns = [
    path('inicio_sesion_evaluador', views.inicio_sesion_evaluador, name='inicio_sesion_evaluador'),
    path('principal/<int:evaluador_id>/', views.principal_evaluador, name='principal_evaluador'),
    path('ver_participantes/<int:evento_id>/', views.ver_participantes, name='ver_participantes'),
    
    # ✅ Parámetros con nombres correctos
    path('evaluar_participante/<int:evento_id>/<int:participante_id>/<int:evaluador_id>/', views.evaluar_participante, name='evaluar_participante'),

    path('criterio/eliminar/<int:criterio_id>/', views.eliminar_criterio, name='eliminar_criterio'),
    path('criterio/modificar/<int:criterio_id>/', views.modificar_criterio, name='modificar_criterio'),
    path('evento/<int:evento_id>/criterios/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('criterios/<int:evento_id>/', views.criterios_evaluacion, name='criterios_evento'),
]



    
    