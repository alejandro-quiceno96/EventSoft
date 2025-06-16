from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app_criterios.models import Criterios
from django.shortcuts import render, get_object_or_404,  redirect
from app_participante.models import Participantes
from .models import Evaluadores
from django.contrib import messages
from app_eventos.models import ParticipantesEventos, EvaluadoresEventos,Eventos
from .models import Calificaciones
from django.db.models import Avg,F
from decimal import Decimal, InvalidOperation
from django.urls import reverse

def principal_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    
    # Traemos las relaciones EvaluadoresEventos para ese evaluador, incluyendo los eventos relacionados
    evaluadores_eventos = EvaluadoresEventos.objects.filter(eva_eve_evaluador_fk=evaluador).select_related('eva_eve_evento_fk')
    
    # Pasamos ese queryset al contexto
    return render(request, 'app_evaluador/inicio_evaluador.html', {
        'evaluador': evaluador,
        'eventos': evaluadores_eventos
    })



def inicio_sesion_evaluador(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        try:
            evaluador = Evaluadores.objects.get(eva_cedula=cedula)
            request.session['evaluador_id'] = evaluador.id  # Guarda el evaluador en la sesión
            request.session['evaluador_nombre'] = evaluador.eva_nombre  # Guarda el evaluador en la sesión
            return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador.id)
        except Evaluadores.DoesNotExist:
            messages.error(request, 'No se encontró ningún evaluador con esa cédula.')
            return redirect('app_evaluador:inicio_sesion_evaluador')
    return render(request, 'app_evaluador/inicio_sesion_evaluador.html')


def ver_participantes(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    participantes_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento)
    evaluador_id = request.session.get('evaluador_id')

    # Participantes evaluados por este evaluador
    calificados_ids = Calificaciones.objects.filter(
        cal_evaluador_fk_id=evaluador_id,
        cal_criterio_fk__cri_evento_fk=evento
    ).values_list('clas_participante_fk_id', flat=True).distinct()

    evaluados_dict = {pid: True for pid in calificados_ids}

    # Ranking
    ranking = participantes_evento.filter(par_eve_calificacion_final__isnull=False).order_by('-par_eve_calificacion_final')

    context = {
        'evento': evento,
        'participantes': participantes_evento,
        'evaluador_nombre': request.session.get('evaluador_nombre'),
        'evaluador': evaluador_id,
        'ranking': ranking,
        'evaluados_dict': evaluados_dict,
    }

    return render(request, 'app_evaluador/participantes_evento.html', context)


def evaluar_participante(request, evento_id, participante_id, evaluador_id):
    participante = get_object_or_404(Participantes, id=participante_id)
    evento = get_object_or_404(Eventos, id=evento_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    criterios = Criterios.objects.filter(cri_evento_fk=evento)

    if request.method == 'POST':
        nuevas_calificaciones = []
        for criterio in criterios:
            puntaje_str = request.POST.get(f'puntaje_{criterio.id}')
            comentario = request.POST.get(f'comentario_{criterio.id}', '').strip()

            if puntaje_str:
                try:
                    puntaje = float(puntaje_str)
                    if 0 <= puntaje <= 100:
                        calificacion = Calificaciones(
                            cal_valor=puntaje,
                            cal_comentario=comentario,
                            cal_criterio_fk=criterio,
                            clas_participante_fk=participante,
                            cal_evaluador_fk=evaluador
                        )
                        nuevas_calificaciones.append(calificacion)
                except ValueError:
                    continue

        Calificaciones.objects.bulk_create(nuevas_calificaciones)

        # --- Cálculo del promedio ponderado con subconsulta y diccionario ---
        subquery = (
            Calificaciones.objects
            .filter(clas_participante_fk=participante)
            .values('clas_participante_fk', 'cal_criterio_fk')
            .annotate(promedio_criterio=Avg('cal_valor'))
        )

        ranking_dict = {}

        for row in subquery:
            criterio = Criterios.objects.filter(id=row['cal_criterio_fk'], cri_evento_fk=evento).first()
            if criterio:
                # promedio ponderado para ese criterio
                ponderado = row['promedio_criterio'] * (criterio.cri_peso / 100)
                ranking_dict[participante.id] = ranking_dict.get(participante.id, 0) + ponderado

        promedio_final = ranking_dict.get(participante.id, 0)

        # Actualizar ParticipantesEventos
        participante_evento = ParticipantesEventos.objects.filter(
            par_eve_participante_fk=participante,
            par_eve_evento_fk=evento
        ).first()

        if participante_evento:
            participante_evento.par_eve_calificacion_final = round(promedio_final, 2)
            participante_evento.save()

        messages.success(request, "Evaluación guardada correctamente.")
        return redirect(reverse('app_evaluador:ver_participantes', kwargs={'evento_id': evento.id}) + '?calificacion=realizada')

    context = {
        'participante': participante,
        'evento': evento,
        'evaluador': evaluador,
        'evaluador_nombre': request.session.get('evaluador_nombre'),
        'criterios': criterios
    }
    return render(request, 'app_evaluador/evaluar_participante.html', context)


def criterios_evaluacion(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    # Obtener los participantes del evento con su calificación final
    participantes_evento = ParticipantesEventos.objects.filter(
        par_eve_evento_fk=evento,
        par_eve_calificacion_final__isnull=False
    ).select_related('par_eve_participante_fk').order_by('-par_eve_calificacion_final')

    # Construir lista para el ranking
    ranking = []
    for p in participantes_evento:
        participante = p.par_eve_participante_fk
        ranking.append({
            'id': participante.id,
            'nombre': participante.par_nombre,
            'promedio': round(p.par_eve_calificacion_final, 2)
        })

    return render(request, 'app_evaluador/evaluador.html', {
        'ranking': ranking,
        'evento': evento,
        'evaluador': request.session.get('evaluador_nombre'),
        'evaluador_id': request.session.get('evaluador_id'),
        
    })
   

    
def obtener_calificaciones(request, evento_id, participante_id, evaluador_id):
    calificaciones = Calificaciones.objects.filter(
        cal_criterio_fk__cri_evento_fk__id=evento_id,
        clas_participante_fk__id=participante_id,
        cal_evaluador_fk__id=evaluador_id
    ).select_related('cal_criterio_fk')

    data = [
        {
            'criterio': c.cal_criterio_fk.cri_descripcion,
            'peso': c.cal_criterio_fk.cri_peso,
            'puntaje': c.cal_valor,
            'comentario': c.cal_comentario or ''
        }
        for c in calificaciones
    ]
    return JsonResponse({'calificaciones': data})