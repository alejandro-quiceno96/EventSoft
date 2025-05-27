from django.shortcuts import render, redirect
from app_eventos.models import ParticipantesEventos
from app_participante.models import Participantes
from django.http import JsonResponse, Http404
from app_eventos.models import Eventos
from app_evaluador.models import Evaluadores
from django.urls import reverse

def info_participantes_eventos(request):
    contexto = {}
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        participante = Participantes.objects.filter(par_cedula=cedula).first()
        if participante:
            eventos_inscritos = ParticipantesEventos.objects.filter(par_eve_participante_fk=participante)
            contexto['participante'] = participante
            contexto['eventos'] = eventos_inscritos
        else:
            contexto['mensaje'] = "No se encontró el participante con esa cédula."
            contexto['cedula'] = cedula
    return render(request, 'app_participantes/ver_info_participante.html', contexto)

def buscar_participantes(request):
    contexto = {}
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        participante = Participantes.objects.filter(par_cedula=cedula).first()
        contexto['cedula'] = cedula
        if participante:
            eventos_inscritos = ParticipantesEventos.objects.filter(par_eve_participante_fk=participante)
            contexto['eventos'] = eventos_inscritos
        else:
            contexto['mensaje'] = "No se encontró participante con esa cédula."
    return render(request, 'app_participantes/buscar_participantes.html', contexto)


def cancelar_inscripcion(request):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')
        cedula = request.POST.get('participante_cedula')
        # Lógica para cancelar la inscripción
        # ...
        return redirect('app_participantes/buscar_participantes.html')
    return redirect('app_participantes/buscar_participantes.html')
    
def modificar_inscripcion(request):
    if request.method == 'POST':
        # Aquí obtén datos del formulario
        evento_id = request.POST.get('evento_id')
        cedula = request.POST.get('participante_cedula')
        # Lógica para modificar inscripción
        # ...
        return redirect('app_participantes/buscar_participantes.html')  # o la vista que corresponda
    return redirect('app_participantes/buscar_participantes.html')
def modificar_inscripcion(request):
    if request.method == 'POST':
        # Aquí obtén datos del formulario
        evento_id = request.POST.get('evento_id')
        cedula = request.POST.get('participante_cedula')
        # Lógica para modificar inscripción
        # ...
        return redirect('app_participantes/buscar_participantes.html')  # o la vista que corresponda
    return redirect('app_participantes/buscar_participantes.html')

def api_detalle_evento(request, evento_id):
    try:
        evento = Eventos.objects.get(pk=evento_id)
    except Eventos.DoesNotExist:
        raise Http404("Evento no encontrado")

    participantes_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento)

    data = []
    for participante_evento in participantes_evento:
        participante = participante_evento.par_eve_participante_fk
        data.append({
            "nombre": getattr(participante, "nombre", "Sin nombre"),  # Cambia 'nombre' por el campo real del modelo Participantes
            "cedula": getattr(participante, "par_cedula", "Sin cédula"),
            "fecha_inscripcion": participante_evento.par_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            "estado": participante_evento.par_eve_estado,
            # Puedes añadir más campos que necesites
        })

    return JsonResponse({"evento": evento.eve_nombre, "participantes": data})

def validar_evaluador(request):
    contexto = {}
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        evaluador = Evaluadores.objects.filter(eva_cedula=cedula).first()
        if evaluador:
            # Redirigir a la app_evaluador, por ejemplo a su dashboard o perfil
            # Aquí puedes construir la URL con reverse y pasar la cédula u otro dato si es necesario
            return redirect(reverse('app_evaluador:dashboard', args=[evaluador.eva_cedula]))
        else:
            contexto['error'] = "Cédula no registrada como evaluador."
    return render(request, 'tu_template.html', contexto)