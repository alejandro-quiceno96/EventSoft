# app_asistente/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),


    # Asistentes
    path('asistente/<int:evento_id>/', views.preinscribir_asistente, name='preinscribir_asistente'),
    path('registrar_asistente/', views.registrar_asistente, name='registrar_asistente'),
    path('cancelar_inscripcion_asistente/<int:evento_id>/', views.cancelar_inscripcion_asistente, name='cancelar_inscripcion_asistente'),
    path('evento_asistentes/<int:evento_id>/<int:asistente_id>/', views.evento_asistentes, name='evento_asistentes'),

    # QR y descargas
    path('qr_asistentesz/<int:evento_id>/', views.qr_asistentesz_ver, name='qr_asistentesz_ver'),
    path('descargar_qr_asistente/<int:evento_id>/', views.descargar_qr_asistente, name='descargar_qr_asistente'),
    path('descargar_programacion/<int:evento_id>/', views.descargar_programacion, name='descargar_programacion'),

    # Búsqueda
    path('Buscar_eventos_asis/', views.eventos_pre_asistente, name='eventos_pre_asistente'),
]

