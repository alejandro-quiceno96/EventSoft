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
from decimal import Decimal, InvalidOperation

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
        cedula = request.POST.get('cedula')
        try:
            evaluador = Evaluadores.objects.get(eva_cedula=cedula)
            request.session['evaluador_id'] = evaluador.id  # Guarda el evaluador en la sesión
            return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador.id)
        except Evaluadores.DoesNotExist:
            messages.error(request, 'No se encontró ningún evaluador con esa cédula.')
            return redirect('app_evaluador:inicio_sesion_evaluador')
    return render(request, 'app_evaluador/inicio_sesion_evaluador.html')


def ver_participantes(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    participantes_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento)
    participantes = [pe.par_eve_participante_fk for pe in participantes_evento]

    # Obtener evaluador_id de la sesión de forma segura
    evaluador_id = request.session.get('evaluador_id')

    if not evaluador_id:
        messages.error(request, "Sesión del evaluador no encontrada. Por favor, inicie sesión.")
        return redirect('app_evaluador:inicio_sesion_evaluador')

    ranking_qs = (
        Calificaciones.objects
        .filter(clas_participante_fk__in=participantes)
        .values('clas_participante_fk')
        .annotate(
            nombre=F('clas_participante_fk__par_nombre'),
            promedio=Avg('cal_valor')
        )
        .order_by('-promedio')
    )
    ranking = list(ranking_qs)

    context = {
        'evento': evento,
        'participantes': participantes,
        'evaluador_id': evaluador_id,
        'ranking': ranking,
    }

    return render(request, 'app_evaluador/participantes_evento.html', context)



def evaluar_participante(request, evento_id, participante_id, evaluador_id):
    participante = get_object_or_404(Participantes, id=participante_id)
    evento = get_object_or_404(Eventos, id=evento_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

    criterios = Criterios.objects.filter(cri_evento_fk=evento)

    if request.method == 'POST':
        for criterio in criterios:
            puntaje_str = request.POST.get(f'puntaje_{criterio.id}')
            if puntaje_str:
                try:
                    puntaje = float(puntaje_str)
                    if 0 <= puntaje <= 100:
                        Calificaciones.objects.create(
                            cal_valor=puntaje,
                            cal_criterio_fk=criterio,
                            clas_participante_fk=participante,
                            cal_evaluador_fk=evaluador
                        )
                except ValueError:
                    continue

        messages.success(request, "Evaluación guardada correctamente.")
        return redirect('app_evaluador:ver_participantes', evento_id=evento.id)

    context = {
        'participante': participante,
        'evento': evento,
        'evaluador': evaluador,
        'criterios': criterios
    } 
    return render(request, 'app_evaluador/evaluar_participante.html', context)

def criterios_evaluacion(request, evento_id):
    evento_actual = get_object_or_404(Eventos, pk=evento_id)
    
    if request.method == 'POST':
        descripcion = request.POST.get('criterio')
        porcentaje = request.POST.get('porcentaje')
        
        try:
            porcentaje_decimal = Decimal(porcentaje)
        except (InvalidOperation, TypeError):
            porcentaje_decimal = None
        
        if descripcion and porcentaje_decimal is not None and 0 <= porcentaje_decimal <= 100:
            nuevo_criterio = Criterios.objects.create(
                cri_descripcion=descripcion,
                cri_peso=porcentaje_decimal,
                cri_evento_fk=evento_actual
            )
            nuevo_criterio.save()
            return redirect('app_evaluador:criterios_evento', evento_id=evento_actual.id)
        else:
            # Podrías agregar un mensaje de error aquí con Django messages
            pass
    
    criterios = Criterios.objects.filter(cri_evento_fk=evento_actual)
    porcentaje_total = sum(c.cri_peso for c in criterios)
    
    context = {
        'evento_actual': evento_actual,
        'criterios': criterios,
        'porcentaje_total': porcentaje_total,
        'evaluador_nombre': request.user.username,
    }
    
    return render(request, 'app_evaluador/evaluador.html', context)





@csrf_exempt
def eliminar_criterio(request, criterio_id):
    if request.method == 'POST':
        criterio = get_object_or_404(Criterios, id=criterio_id)
        criterio.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def modificar_criterio(request, criterio_id):
    if request.method == 'POST':
        criterio = get_object_or_404(Criterios, id=criterio_id)
        descripcion = request.POST.get('descripcion')
        peso = request.POST.get('peso')
        from decimal import Decimal, InvalidOperation
        try:
            peso_decimal = Decimal(peso)
        except (InvalidOperation, TypeError):
            return JsonResponse({'success': False, 'error': 'Peso inválido'})

        if descripcion and 0 <= peso_decimal <= 100:
            criterio.cri_descripcion = descripcion
            criterio.cri_peso = peso_decimal
            criterio.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})