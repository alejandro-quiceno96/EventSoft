from django.urls import path
from . import views

urlpatterns = [
    path('buscar/', views.buscar_participante, name='buscar_participante'),
    path('cancelar/', views.cancelar_pre_par, name='cancelar_pre_par'),
    path('eventos/', views.eventos_participante, name='eventos_participante'),
    path('modificar/', views.modificar_participante, name='modificar_participante'),
    path('preinscripcion/', views.pre_inscripcion, name='pre_inscripcion'),
    path('ver_info/', views.ver_info_participante, name='ver_info_participante'),
]
