from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from app_eventos.models import Eventos, AsistentesEventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase
from app_eventos.models import Eventos,  ParticipantesEventos, EvaluadoresEventos
from django.views.decorators.csrf import csrf_exempt
from app_participante.models import Participantes
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores
from django.utils import timezone
from django.urls import reverse
from app_administrador.utils import generar_pdf, generar_clave_acceso
import json
from django.http import JsonResponse

def inicio_visitante(request):
    eventos = Eventos.objects.all()

    categoria = request.GET.get('categoria')
    area = request.GET.get('area')
    fecha_inicio = request.GET.get('fecha_inicio')

    print("GET data:", request.GET)

    # Filtrar por categoría (a través del modelo intermedio)
    if categoria:
        eventos = eventos.filter(eventoscategorias__eve_cat_categoria_fk=categoria)

    # Filtrar por área (a través de categoria relacionada al evento)
    if area:
        eventos = eventos.filter(
            eventoscategorias__eve_cat_categoria_fk__cat_area_fk=area
        )

    # Filtrar por fecha de inicio
    if fecha_inicio:
        eventos = eventos.filter(eve_fecha_inicio=fecha_inicio)

    eventos = eventos.distinct()  # Evitar duplicados por joins

    categorias = Categorias.objects.all()
    areas = Areas.objects.all()

    contexto = {
        'eventos': eventos,
        'categorias': categorias,
        'areas': areas,
    }

    return render(request, 'app_visitante/index.html', contexto)





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

def preinscripcion_evaluador(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    return render(request, 'app_visitante/preinscripcion_evaluador.html', {'evento': evento})

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

        # Verificar si el participante ya existe
        try:
            participante = Participantes.objects.get(par_cedula=par_cedula)
        except Participantes.DoesNotExist:
            # Si no existe, crear un nuevo participante
            participante = Participantes.objects.create(
                par_nombre=par_nombre,
                par_cedula=par_cedula,
                par_correo=par_correo,
                par_telefono=par_telefono,
            )

        # Obtener el evento
        try:
            evento = Eventos.objects.get(pk=evento_id)
        except Eventos.DoesNotExist:
            # Si el evento no existe, redirigir a una página de error o inicio
            return redirect('inicio_visitante')

        # Crear la inscripción del participante al evento
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=participante,
            par_eve_evento_fk=evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=documento,
            par_eve_estado='Pendiente',  # Puedes cambiar este valor según tu lógica
            par_eve_qr='',  # Debes subir o generar uno real
            par_eve_clave=''  # Idealmente deberías generar una clave segura
        )

        # Redirigir a la página de inicio del visitante
        return redirect(reverse('inicio_visitante') + '?registro=exito_participante')

    # Si no es POST, redirigir a la página de inicio del visitante
    return redirect('inicio_visitante')




def registrar_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    if request.method == 'POST':
        cedula = request.POST.get('numero_identificacion')
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        documento = request.FILES.get('comprobante_pago')
        
        asistente_existente = Asistentes.objects.filter(asi_cedula=cedula).first()

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

                
    return redirect(reverse('inicio_visitante') + '?registro=exito_asistente')

def registrar_evaluador(request, evento_id):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        cedula = request.POST.get('cedula')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        documento = request.FILES.get('documento')

        try:
            evaluador = Evaluadores.objects.get(eva_cedula=cedula)
        except Evaluadores.DoesNotExist:
            evaluador = Evaluadores.objects.create(
                eva_nombre=nombre,
                eva_cedula=cedula,
                eva_correo=correo,
                eva_telefono=telefono,
            )

        try:
            evento = Eventos.objects.get(id=evento_id)
        except Eventos.DoesNotExist:
            return redirect('inicio_visitante')

        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=evaluador,
            eva_eve_evento_fk=evento,
            eva_eve_fecha_hora=timezone.now(),
            eva_eve_documentos=documento,
            eva_estado='Pendiente',
            eva_eve_qr='',
        )

        # Redirige agregando un parámetro ?registro=exito
        return redirect(reverse('inicio_visitante') + '?registro=exito_evaluador')

    return redirect('inicio_visitante')



respuestas = {
    "hola": "¡Hola! Soy el asistente virtual de EventSoft. ¿En qué puedo ayudarte?",
    "que hace un participante?": "Un participante puede asistir a conferencias, talleres y recibir certificados de participación.",
    "que hace un visitante?": "Un visitante puede recorrer el evento, conocer los stands, pero no participa en las actividades certificadas.",
    "cómo me inscribo?": "Puedes inscribirte desde la página principal, usando el botón de inscripción o accediendo con tu número de documento.",
    "cuáles son los eventos disponibles?": "Puedes ver los eventos disponibles en la sección principal o usar los filtros por categoría y área.",
    "documentos": "Para participar solo necesitas tu documento de identidad y, si aplica, la invitación del evento.",
}

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        mensaje = data.get("mensaje", "").lower()

        for clave, respuesta in respuestas.items():
            if clave in mensaje:
                return JsonResponse({"respuesta": respuesta})

        return JsonResponse({"respuesta": "Lo siento, no entendí tu pregunta. ¿Podrías reformularla?"})
