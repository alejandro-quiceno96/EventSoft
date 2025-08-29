from django.urls import path
from . import views

app_name = 'super_admin'

urlpatterns = [ 
    
    path('', views.index, name='index_super_admin'),
    path('evento_adm/<int:evento_id>/', views.ver_evento_adm, name='ver_evento_adm'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('modificar_evento/<int:evento_id>/<str:nuevo_estado>', views.modificar_estado_evento, name='modificar_eventos'),
    path('usuarios/', views.gestionar_usuarios, name='usuarios'),
    path("asignar-admin/", views.asignar_admin_evento, name="asignar_admin_evento"),
    path('cancelar-administrador/', views.cancelar_administrador, name='cancelar_administrador'),
    path('estadisticas-evento/<int:evento_id>/', views.obtener_estadisticas_evento, name='estadisticas_evento'),
    path('cancelar-evento/<int:evento_id>/', views.cancelar_evento, name='cancelar_evento'),
    path('eliminar-evento/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
    path("crear_area/", views.crear_area, name="crear_area"),
    path("crear_categoria/", views.crear_categoria, name="crear_categoria"),




]