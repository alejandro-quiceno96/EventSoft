from django.urls import path
from . import views
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase

urlpatterns = [
    path('', views.inicio_visitante, name='inicio_visitante'),
    path('evento/<int:evento_id>/', views.ver_evento, name='ver_evento'),

]
