
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_visitante.urls')),
    path('asistente/', include('app_asistente.urls')),
    path('administrador/', include('app_administrador.urls')),
    path('inicio_administrador/', include('app_administrador.urls')),
    path('ver_evento/', include('app_visitante.urls')),
   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
