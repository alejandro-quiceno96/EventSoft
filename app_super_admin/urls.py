from django.urls import path
from . import views

app_name = 'super_admin'

urlpatterns = [ 
    
    path('', views.index, name='index_super_admin'),
    path('evento_adm/<int:evento_id>/', views.ver_evento_adm, name='ver_evento_adm'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('modificar_evento/<int:evento_id>/<str:nuevo_estado>', views.modificar_estado_evento, name='modificar_eventos'),
]