
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app_visitante import views as visitante_views
from django.contrib.auth import views as auth_views


LOGIN_URL = '/admin/login/' 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_visitante.urls')),
    path('asistente/', include('app_asistente.urls', namespace = "app_asistente")),
    path('administrador/', include('app_administrador.urls', namespace='administrador'), ),
    path('participante/', include('app_participante.urls', namespace='app_participante')),
    path('super_admin/', include(('app_super_admin.urls', 'super_administrador'), namespace='super_administrador')),
    path('evaluador/', include('app_evaluador.urls', namespace='app_evaluador')),
    #Tests que se necesitan parque corran 
    path('visitante/', visitante_views.inicio_visitante, name='inicio_visitante'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
      # o la URL de tu vista de login

]



urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
