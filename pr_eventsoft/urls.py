
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_visitante.urls')),
    path('asistente/', include('app_asistente.urls')),
    path('administrador/', include('app_administrador.urls', namespace='administrador'), ),
    path('ver_evento/', include('app_visitante.urls')),
    path('participante/', include('app_participante.urls', namespace='app_participante')),
    path('super_admin/', include(('app_super_admin.urls', 'super_administrador'), namespace='super_administrador')),
    path('evaluador/', include('app_evaluador.urls', namespace='evaluador')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
