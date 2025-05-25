from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'administrador'

urlpatterns=[
    path('', views.inicio, name='index_administrador' ),
    path('crear_evento/', views.crear_evento, name='crear_evento' ),
    path('get_categorias/<int:area_id>', views.get_categorias, name='get_categorias' ),
    path('event/<int:evento_id>', views.obtener_evento, name='evento_detalle'),
    path('eliminar/<int:evento_id>', views.eliminar_evento, name='eliminar_evento'),
    path('inicio_sesion/', views.inicio_sesion_administrador, name='inicio_sesion_administrador'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

