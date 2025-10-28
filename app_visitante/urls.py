from django.urls import path
from . import views
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase

urlpatterns = [
    path('', views.inicio_visitante, name='inicio_visitante'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_usuario_view, name='registro'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('verificar-documento/', views.verificar_documento, name='verificar_documento'),
    path('confirmar-rol/', views.confirmar_rol, name='confirmar_rol'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('evento/<int:evento_id>/', views.detalle_evento, name='detalle_evento'),
    path('preinscripcion_participante/<int:evento_id>/', views.preinscripcion_participante, name='preinscripcion_participante'),
    path('preinscripcion_asistente/<int:evento_id>/', views.preinscripcion_asistente, name='preinscripcion_asistente'),
    path('preinscripcion_evaluador/<int:evento_id>/', views.preinscripcion_evaluador, name='preinscripcion_evaluador'),
    path('modificar_participante/', views.modificar_participante, name='modificar_participante'),
    path('submit_preinscripcion/', views.submit_preinscripcion_participante, name='submit_preinscripcion_participante'),
    path('guardar_evaluador/<int:evento_id>/', views.registrar_evaluador, name='registrar_evaluador'),
    path('registro/<int:evento_id>/', views.registrar_asistente, name='registrar_asistente'),
    path('inicio_evaluado/', views.inicio_evaluador, name='inicio_sesion_evaluador'),
    path("chatbot/", views.chatbot, name="chatbot"),
    path('validar-clave-admin/', views.validar_clave_admin, name='validar_clave_admin'),
    path('Recuperar-contraseña', views.recuperar_contraseña, name='recuperar_contraseña'),
    path('proyectos/<str:codigo>', views.buscar_proyecto, name='buscar_proyecto'),

]
