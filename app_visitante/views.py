from django.shortcuts import render
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase

# Create your views here.


def inicio_visitante(request):
    eventos = Eventos.objects.all()
    categorias = Categorias.objects.all()
    areas = Areas.objects.all()
    contexto = {
        'eventos': eventos,
        'categorias': categorias,
        'areas': areas,
    }
    return render(request, 'app_visitante/base.html', contexto)
def ver_evento(request, evento_id):
    # lógica aquí
    return render(request, 'ver_evento.html', {'evento_id': evento_id})