from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from app_eventos.models import Eventos, AsistentesEventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase
from app_eventos.models import Eventos
from django.views.decorators.csrf import csrf_exempt
from app_participante.models import Participantes
from app_asistente.models import Asistentes
from django.utils import timezone
from app_eventos.models import ParticipantesEventos
from app_administrador.utils import generar_pdf, generar_clave_acceso

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
    return render(request, 'app_visitante/inicio_sesion_administrador.html')

def inicio_evaluador(request):
    return render(request, 'app_visitante/inicio_sesion_evaluador.html')

def detalle_evento(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)
    return render(request, 'app_visitante/detalle_evento.html', {'evento': evento})



def preinscripcion_participante(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    return render(request, 'app_visitante/Pre_inscripcion_participante.html', {'evento': evento})

def preinscripcion_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    return render(request, 'app_visitante/registro_asistente.html', {'evento': evento})

def modificar_participante(request):
    return render(request, 'app_visitante/modificar_participante.html')





def submit_preinscripcion_participante(request):
    if request.method == 'POST':
        par_nombre = request.POST.get('par_nombre')
        par_cedula = request.POST.get('par_cedula')
        par_correo = request.POST.get('par_correo')
        par_telefono = request.POST.get('par_telefono')
        documento = request.FILES.get('par_eve_documentos')
        evento_id = request.POST.get('evento_id')

        participante = Participantes.objects.create(
            par_nombre=par_nombre,
            par_cedula=par_cedula,
            par_correo=par_correo,
            par_telefono=par_telefono,
        )

        evento = Eventos.objects.get(pk=evento_id)

        ParticipantesEventos.objects.create(
            par_eve_participante_fk=participante,
            par_eve_evento_fk=evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=documento,
            par_eve_estado='Pendiente',  # Puedes cambiar este valor según tu lógica
            par_eve_qr='',  # Debes subir o generar uno real
            par_eve_clave=''  # Idealmente deberías generar una clave segura
        )

        return redirect('inicio_visitante')

    return redirect('inicio_visitante')



def registrar_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    if request.method == 'POST':
        cedula = request.POST.get('numero_identificacion')
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        documento = request.FILES.get('comprobante_pago')
        
        asistente_existente = asistente = Asistentes.objects.filter(asi_cedula=cedula).first()

       # Crear o usar asistente existente
        if asistente_existente:
            asistente = asistente_existente
        else:
            asistente = Asistentes.objects.create(
                asi_cedula=cedula,
                asi_nombre=nombre,
                asi_correo=correo,
                asi_telefono=telefono
            )
            asistente.save()

        # Crear la inscripción del asistente al evento
        if evento.eve_tienecosto:
            estado = 'Pendiente'
            qr = ''
            clave = ''
        else:
            estado = 'Admitido'
            qr = generar_pdf(cedula, 'Asistente', evento_id, tipo="asistente")
            clave = generar_clave_acceso()

        asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=asistente,
            asi_eve_evento_fk=evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_soporte=documento,
            asi_eve_estado=estado,
            asi_eve_qr=qr,
            asi_eve_clave=clave
        )
        asistente_evento.save()

                
    return redirect('detalle_evento', evento_id=evento_id)
