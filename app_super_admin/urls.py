from django.urls import path
from . import views

app_name = 'super_admin'

urlpatterns = [ 
    
    path('', views.index, name='index'),
    path('evento_adm/<int:evento_id>/', views.ver_evento_adm, name='ver_evento_adm'),
    path('inicio_sesion_super_admin/', views.inicio_sesion_super_admin, name='inicio_sesion_super_admin'),
]