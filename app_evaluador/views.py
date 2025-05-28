from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app_criterios.models import Criterios
from django.shortcuts import render, get_object_or_404,  redirect
from app_eventos.models import Eventos
from app_participante.models import Participantes
from .models import Evaluadores
from django.contrib import messages
from app_eventos.models import ParticipantesEventos
from .models import Calificaciones
from django.db.models import Avg,F

def principal_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    eventos = Eventos.objects.all()  # O puedes filtrar según el evaluador, si aplica
    return render(request, 'app_evaluador/inicio_evaluador.html', {
        'evaluador': evaluador,
        'eventos': eventos
    })


@csrf_exempt
def eliminar_criterio(request, criterio_id):
    if request.method == 'POST':
        try:
            criterio = Criterios.objects.get(id=criterio_id)
            criterio.delete()
            return JsonResponse({'success': True})
        except Criterios.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Criterio no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def asignar_puntaje(request, evento_id, participante_id, evaluador_id):
    if request.method == 'POST':
        puntajes = request.POST.getlist('puntajes')
        
        ...
    ...

def evaluar_participante(request, evento_id, participante_id, evaluador_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    participante = get_object_or_404(Participantes, id=participante_id)
    evaluador = evaluador_id  # o si tienes un modelo Evaluador, búscalo también

    # Renderizas el template con el contexto necesario
    return render(request, 'evaluar_participante.html', {
        'evento': evento,
        'participante': participante,
        'evaluador': evaluador,
    })

def inicio_sesion_evaluador(request):
    if request.method == 'POST':
        cedula = request.POST.get('eva_cedula')
        try:
            evaluador = Evaluadores.objects.get(eva_cedula=cedula)
            request.session['evaluador_id'] = evaluador.id  # Guarda el evaluador en la sesión
            return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador.id)
        except Evaluadores.DoesNotExist:
            messages.error(request, 'No se encontró ningún evaluador con esa cédula.')
            return redirect('app_evaluador:inicio_sesion_evaluador')
    return render(request, 'app_evaluador/inicio_sesion_evaluador.html')



def ver_participantes(request, evento_id):
    # Obtener el evento o 404
    evento = get_object_or_404(Eventos, id=evento_id)
    
    # Obtener los participantes admitidos en ese evento
    participantes_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento)
    
    # Extraer los participantes (model Participantes) desde ParticipantesEventos
    participantes = [pe.par_eve_participante_fk for pe in participantes_evento]
    
    # Obtener evaluador actual (si lo tienes en sesión, por ejemplo)
    evaluador = request.user.id   # Ajusta según tu lógica
    
    # Calcular ranking con promedio de calificaciones por participante en este evento
    # Suponiendo que Calificaciones tiene campo clas_participante_fk que apunta a Participantes
    
    ranking_qs = (
        Calificaciones.objects
        .filter(clas_participante_fk__in=participantes)
        .values('clas_participante_fk')  # agrupar por participante
        .annotate(
            nombre=F('clas_participante_fk__par_nombre'),  # usar el campo real
            promedio=Avg('cal_valor')
        )
        .order_by('-promedio')
    )
    ranking = list(ranking_qs)
    
    context = {
        'evento': evento,
        'participantes': participantes,
        'evaluador': evaluador,
        'ranking': ranking,
    }   
    
    return render(request, 'app_evaluador/participantes_evento.html', context)



def evaluar_participante(request, evento_id, participante_id, evaluador_id):
    participante = get_object_or_404(Participantes, id=participante_id)
    evento = get_object_or_404(Eventos, id=evento_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

    if request.method == 'POST':
        # Lógica de evaluación
        pass

    context = {
        'participante': participante,
        'evento': evento,
        'evaluador': evaluador,
    }
    return render(request, 'app_evaluador/evaluar_participante.html', context)
