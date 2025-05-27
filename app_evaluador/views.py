from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app_criterios.models import Criterios
from django.shortcuts import render, get_object_or_404,  redirect
from app_eventos.models import Eventos
from app_participante.models import Participantes
from .models import Evaluadores
from django.contrib import messages

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

def inicio_sesion(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        try:
            evaluador = Evaluadores.objects.get(cedula=cedula)
            # Redirige a la página principal del evaluador o dashboard
            return redirect('evaluador:home', evaluador_id=evaluador.id)
        except Evaluadores.DoesNotExist:
            messages.error(request, 'No se encontró ningún evaluador con esa cédula.')
            return redirect('app_evaluador:inicio_sesion')

    return render(request, 'evaluador/inicio_sesion.html')
