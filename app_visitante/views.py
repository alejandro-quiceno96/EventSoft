from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase
from app_eventos.models import Eventos
from django.views.decorators.csrf import csrf_exempt
from app_participante.models import Participantes
from django.contrib import messages
from app_asistente.models import AsistenteEvento, Asistentes
from django.utils import timezone
from .forms import RegistroAsistenteForm


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



def inicio_sesion_administrador(request):
    return render(request, 'app_administrador/inicio_sesion.html')

def detalle_evento(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)
    return render(request, 'app_visitante/detalle_evento.html', {'evento': evento})



def preinscripcion_participante(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)
    return render(request, 'app_visitante/Pre_inscripcion_participante.html', {'evento': evento})

def preinscripcion_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)
    return render(request, 'app_visitante/registro_asistente.html', {'evento': evento})

def modificar_participante(request):
    return render(request, 'app_visitante/modificar_participante.html')





def submit_preinscripcion_participante(request):
    if request.method == 'POST':
        par_nombre = request.POST.get('par_nombre')
        par_cedula = request.POST.get('par_cedula')
        par_correo = request.POST.get('par_correo')
        par_telefono = request.POST.get('par_telefono')
        documento = request.FILES.get('documento')

        participante = Participantes(
            par_nombre=par_nombre,
            par_cedula=par_cedula,
            par_correo=par_correo,
            par_telefono=par_telefono,
            documento=documento,
        )
        participante.save()

        # Aquí puedes redirigir a una página de éxito, lista de eventos, o lo que prefieras
        return redirect('inicio_visitante')


    return redirect('inicio_visitante')



def registrar_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    if request.method == 'POST':
        form = RegistroAsistenteForm(request.POST, request.FILES)
        if form.is_valid():
            asistente = form.save()  # Guardas el asistente
            # Creas la relación con el evento
            AsistenteEvento.objects.create(asistente=asistente, evento=evento)
            return redirect('app_visitante/detalle_evento', evento_id=evento.id)
    else:
        form = RegistroAsistenteForm()

    context = {
        'form': form,
        'evento': evento,
    }
    return render(request, 'app_visitante/registro_asistente.html', context)
