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
from app_eventos.models import EventosCategorias
import json
from django.http import HttpResponse
from weasyprint import HTML
from app_categorias.models import Categorias
from django.http import JsonResponse, Http404, HttpResponse
from .forms import EvaluadorForm
import os
from django.conf import settings


def principal_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    print(f"Principal Evaluador: {evaluador.eva_nombre} (ID: {evaluador.id})")
    # Traemos las relaciones EvaluadoresEventos para ese evaluador, incluyendo los eventos relacionados
    evaluadores_eventos = EvaluadoresEventos.objects.filter(eva_eve_evaluador_fk=evaluador).select_related('eva_eve_evento_fk')
    
    # Pasamos ese queryset al contexto
    return render(request, 'app_evaluador/inicio_evaluador.html', {
        'evaluador': evaluador,
        'evaluador_id': evaluador_id,
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
        'evaluador_id': request.session.get('evaluador_id'),
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

def buscar_evaluador(request):
    return render(request, 'app_evaluador/buscar_evaluador.html')


def informacion_evaluador(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')

        try:
            evaluador = Evaluadores.objects.get(eva_cedula=cedula)

            # Obtenemos las calificaciones hechas por ese evaluador
            calificaciones = Calificaciones.objects.filter(
                cal_evaluador_fk=evaluador
            ).select_related('clas_participante_fk')  # Ya no ponemos doble relación aquí

            # Extraemos los IDs de eventos relacionados con los participantes calificados
            eventos_ids = set()

            for cal in calificaciones:
                participante_evento = cal.clas_participante_fk
                if hasattr(participante_evento, 'par_eve_evento_fk'):
                    evento = participante_evento.par_eve_evento_fk
                    if evento:
                        eventos_ids.add(evento.id)

            eventos_asignados = Eventos.objects.filter(
                    evaluadoreseventos__eva_eve_evaluador_fk=evaluador
                ).distinct()

            # Cálculo de estadísticas simples
            total_eventos = eventos_asignados.count()
            evaluaciones_completadas = calificaciones.filter(cal_valor__isnull=False).count()
            evaluaciones_pendientes = calificaciones.filter(cal_valor__isnull=True).count()

            contexto = {
                'evaluador': evaluador,
                'eventos_asignados': eventos_asignados,
                'total_eventos': total_eventos,
                'evaluaciones_completadas': evaluaciones_completadas,
                'evaluaciones_pendientes': evaluaciones_pendientes,
            }

            return render(request, 'app_evaluador/info_evaluador.html', contexto)

        except Evaluadores.DoesNotExist:
            return render(request, 'app_evaluador/info_evaluador.html', {
                'evaluador': None,
                'eventos_asignados': [],
                'total_eventos': 0,
                'evaluaciones_completadas': 0,
                'evaluaciones_pendientes': 0,
                'mensaje_error': 'Evaluador no encontrado.',
            })

    return render(request, 'app_evaluador/buscar_evaluador.html')
 

def detalle_evento_json(request, evento_id, evaluador_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    data = {
        'nombre': evento.eve_nombre,
        'descripcion': evento.eve_descripcion,
        'ciudad': evento.eve_ciudad,
        'lugar': evento.eve_lugar,
        'fecha': evento.eve_fecha.strftime('%Y-%m-%d') if evento.eve_fecha else '',
        'estado': evento.eve_estado,
        'imagen': evento.eve_imagen.url if evento.eve_imagen else ''
    }
    return JsonResponse(data)

@csrf_exempt
def obtener_datos_evaluador(request, cedula):
    """Obtener datos del evaluador en formato JSON"""
    try:
        evaluador = Evaluadores.objects.get(eva_cedula=cedula)
        
        datos = {
            "eva_cedula": evaluador.eva_cedula,
            "eva_nombre": evaluador.eva_nombre,
            "eva_correo": evaluador.eva_correo,
            "eva_telefono": evaluador.eva_telefono,
        }
        
        return JsonResponse(datos)
        
    except Evaluadores.DoesNotExist:
        return JsonResponse({"error": "Evaluador no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Error en el servidor: {str(e)}"}, status=500)
    
def editar_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

    eventos_asignados = Eventos.objects.filter(
        evaluadoreseventos__eva_eve_evaluador_fk=evaluador
    ).distinct()

    evento_id = request.GET.get('evento_id') or request.POST.get('evento_id')
    evento = None

    if evento_id:
        try:
            evento = Eventos.objects.get(id=evento_id)
        except Eventos.DoesNotExist:
            messages.warning(request, "El evento no fue encontrado.")
            evento = None

    if request.method == 'POST':
        form = EvaluadorForm(request.POST, instance=evaluador)
        if form.is_valid():
            form.save()
            messages.success(request, "Evaluador actualizado correctamente.")
            
            # Redirección mejorada sin usar reverse con parámetros complejos
            if evento:
                # Construir la URL manualmente para evitar problemas
                redirect_url = f"/evaluador/informacion/?cedula={evaluador.eva_cedula}&evento_id={evento.id}"
                return redirect(redirect_url)
            else:
                # Redirección simple a la página de información del evaluador
                redirect_url = f"/evaluador/informacion/?cedula={evaluador.eva_cedula}"
                return redirect(redirect_url)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = EvaluadorForm(instance=evaluador)

    return render(request, 'app_evaluador/editar_evaluador.html', {
        'form': form,
        'evaluador': evaluador,
        'evento': evento,
        'evento_id': evento_id,
        'eventos_asignados': eventos_asignados,
    })

def detalle_evento_evaluador(request, evento_id, evaluador_cedula):
    """Obtener detalles de un evento para el evaluador"""
    print(f"Recibida petición para evento {evento_id} y evaluador {evaluador_cedula}")
    try:
        evento = Eventos.objects.get(id=evento_id)
        evaluador = Evaluadores.objects.get(eva_cedula=evaluador_cedula)
    except (Eventos.DoesNotExist, Evaluadores.DoesNotExist):
        return JsonResponse({"error": "Evento o evaluador no encontrado"}, status=404)

    # Obtener la categoría relacionada
    categoria_nombre = ""
    try:
        evento_categoria = EventosCategorias.objects.get(eve_cat_evento_fk=evento_id)
        categoria_nombre = evento_categoria.eve_cat_categoria_fk.cat_nombre
    except EventosCategorias.DoesNotExist:
        pass

    datos_evento = {
        'eve_id': evento.id,
        'eve_nombre': evento.eve_nombre,
        'eve_descripcion': evento.eve_descripcion,
        'eve_ciudad': evento.eve_ciudad,
        'eve_lugar': evento.eve_lugar,
        'eve_fecha_inicio': evento.eve_fecha_inicio.strftime('%Y-%m-%d'),
        'eve_fecha_fin': evento.eve_fecha_fin.strftime('%Y-%m-%d'),
        'eve_estado': evento.eve_estado,
        'eve_imagen': evento.eve_imagen.url if evento.eve_imagen else None,
        'eve_capacidad': evento.eve_capacidad if evento.eve_capacidad is not None else 'Cupos ilimitados',
        'eve_costo': 'Con Pago' if evento.eve_tienecosto else 'Sin Pago',
        'eve_programacion': evento.eve_programacion.url if evento.eve_programacion else None,
        'eve_categoria': categoria_nombre,
    }

    return JsonResponse(datos_evento)


def generar_reporte_evaluador(request, cedula):
    """Generar reporte PDF del evaluador"""
    try:
        evaluador = get_object_or_404(Evaluadores, eva_cedula=cedula)
        
        # CORRECCIÓN: Usar select_related de forma segura
        calificaciones = Calificaciones.objects.filter(
            cal_evaluador_fk=evaluador
        ).select_related('clas_participante_fk')
        
        # Obtener eventos únicos donde ha evaluado
        eventos_evaluados = set()
        for cal in calificaciones:
            if hasattr(cal, 'clas_participante_fk') and cal.clas_participante_fk:
                # Ajustar según la estructura real de tu modelo
                if hasattr(cal.clas_participante_fk, 'par_eve_evento_fk'):
                    eventos_evaluados.add(cal.clas_participante_fk.par_eve_evento_fk)
                elif hasattr(cal.clas_participante_fk, 'evento'):
                    eventos_evaluados.add(cal.clas_participante_fk.evento)
        
        # Estadísticas - CORRECCIÓN: Cambiar cal_calificacion por cal_valor
        total_evaluaciones = calificaciones.count()
        evaluaciones_completadas = calificaciones.filter(cal_valor__isnull=False).count()
        
        contexto = {
            'evaluador': evaluador,
            'calificaciones': calificaciones,
            'eventos_evaluados': list(eventos_evaluados),
            'total_evaluaciones': total_evaluaciones,
            'evaluaciones_completadas': evaluaciones_completadas,
        }
        
        # Renderizar template HTML
        html_string = render(request, 'app_evaluador/reporte_evaluador.html', contexto).content.decode('utf-8')
        
        # Generar PDF
        pdf = HTML(string=html_string).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=reporte_evaluador_{evaluador.eva_nombre}.pdf'
        return response
        
    except Exception as e:
        return JsonResponse({"error": f"Error al generar el reporte: {str(e)}"}, status=500)

def participantes_por_evaluar(request, evaluador_cedula, evento_id):  # CORRECCIÓN: Agregar evento_id como parámetro
    """Obtener participantes de un evento que debe evaluar el evaluador"""
    try:
        evaluador = Evaluadores.objects.get(eva_cedula=evaluador_cedula)
        evento = Eventos.objects.get(id=evento_id)
        
        # Obtener participantes del evento
        participantes_evento = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento,
        ).select_related('par_eve_participante_fk')
        
        # CORRECCIÓN: Obtener calificaciones realizadas de forma segura
        calificaciones_realizadas = Calificaciones.objects.filter(
            cal_evaluador_fk=evaluador,
        )
        
        # Crear un set con los IDs de participantes ya evaluados
        participantes_evaluados = set()
        for cal in calificaciones_realizadas:
            if hasattr(cal, 'clas_participante_fk') and cal.clas_participante_fk:
                # Ajustar según la estructura real de tu modelo
                if hasattr(cal.clas_participante_fk, 'par_eve_evento_fk'):
                    if cal.clas_participante_fk.par_eve_evento_fk == evento:
                        participantes_evaluados.add(cal.clas_participante_fk.id)
        
        participantes_data = []
        for par_evento in participantes_evento:
            participante = par_evento.par_eve_participante_fk
            ya_evaluado = par_evento.id in participantes_evaluados
            
            participantes_data.append({
                'par_eve_id': par_evento.id,
                'par_nombre': participante.par_nombre,
                'par_cedula': participante.par_cedula,
                'par_correo': participante.par_correo,
                'par_telefono': participante.par_telefono,
                'estado_inscripcion': par_evento.par_eve_estado,
                'ya_evaluado': ya_evaluado,
                'documento_url': par_evento.par_eve_documentos.url if par_evento.par_eve_documentos else None
            })
        
        return JsonResponse({
            'evaluador': evaluador.eva_nombre,
            'evento': evento.eve_nombre,
            'participantes': participantes_data
        })
        
    except (Evaluadores.DoesNotExist, Eventos.DoesNotExist):
        return JsonResponse({"error": "Evaluador o evento no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Error en el servidor: {str(e)}"}, status=500)
    


def detalle_evento(request, cedula, evento_id):
    try:
        evento = Eventos.objects.get(id=evento_id)
        evaluador = Evaluadores.objects.get(id=cedula)
    except Eventos.DoesNotExist:
        raise Http404("Evento no encontrado")
    evento = get_object_or_404(Eventos, id=evento_id)
    participantes_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento)


    # Obtener la categoría relacionada
    categoria_nombre = ""
    evento = get_object_or_404(Eventos, id=evento_id)

   
    try:
        evento_categoria = EventosCategorias.objects.get(eve_cat_evento_fk=evento_id)
        categoria = Categorias.objects.get(id=evento_categoria.eve_cat_categoria_fk.id)
        categoria_nombre = categoria.cat_nombre
    except (EventosCategorias.DoesNotExist, Categorias.DoesNotExist):
        pass

    # Obtener Clave de acceso
    clave_acceso = None
    try:
        print(f"Buscando clave de acceso para evento {evento_id} y evaluador {cedula}")
        clave_acceso = EvaluadoresEventos.objects.get(eva_eve_evento_fk=evento_id, eva_eve_evaluador_fk=cedula)

    except EvaluadoresEventos.DoesNotExist:
        clave_acceso = None

    datos_evento = {
        'eve_id': evento.id,
        'eve_nombre': evento.eve_nombre,
        'eve_descripcion': evento.eve_descripcion,
        'eve_ciudad': evento.eve_ciudad,
        'eve_lugar': evento.eve_lugar,
        'eve_fecha_inicio': evento.eve_fecha_inicio.strftime('%Y-%m-%d'),
        'eve_fecha_fin': evento.eve_fecha_fin.strftime('%Y-%m-%d'),
        'eve_estado': evento.eve_estado,
        'eve_imagen': evento.eve_imagen.url if evento.eve_imagen else None,
        'eve_cantidad': evento.eve_capacidad if evento.eve_capacidad is not None else 'Cupos ilimitados',
        'eve_costo': 'Con Pago' if evento.eve_tienecosto else 'Sin Pago',
        'eve_programacion': evento.eve_programacion.url if evento.eve_programacion else None,
        'eve_categoria': categoria_nombre, 
        'eve_clave': clave_acceso.eva_clave_acceso if clave_acceso else '',
        'codigo_qr': clave_acceso.eva_eve_qr.url if clave_acceso and clave_acceso.eva_eve_qr else '',
        'cedula': cedula,
        'participantes': participantes_evento,
        'documento': clave_acceso.eva_eve_documentos.url if clave_acceso and clave_acceso.eva_eve_documentos else None,
        'informacion_tecnica': evento.eve_informacion_tecnica.url if evento.eve_informacion_tecnica else None,
    }

    return render(request, 'app_evaluador/detalle_evento.html', {
    'evento': datos_evento,
    'evaluador': evaluador,
    'participantes_evento': participantes_evento,
    'evento_obj': evento, 
})

def inicio_evaluador(request):
    return render(request, 'app_evaluador/inicio_evaluador.html')



def subir_info_tecnica(request, pk):
    if request.method == 'POST':
        evento = get_object_or_404(Eventos, pk=pk)
        evaluador_cedula = request.POST.get('cedula')
        evaluador = get_object_or_404(Evaluadores, eva_cedula=evaluador_cedula)

        if not evaluador_cedula:
            return JsonResponse({'success': False, 'message': 'No se pudo identificar al evaluador.'})

        if 'eve_informacion_tecnica' in request.FILES:
            evento.eve_informacion_tecnica = request.FILES['eve_informacion_tecnica']
            evento.save()
            return redirect('app_evaluador:detalle_evento_evaluador', evento_id=evento.id, cedula=evaluador.id)
        else:
            return JsonResponse({'success': False, 'message': 'No se encontró el archivo a subir.'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


def modificar_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

    if request.method == 'POST':
        nombre = request.POST.get('eva_nombre')
        correo = request.POST.get('eva_correo')
        telefono = request.POST.get('eva_telefono')

        evaluador.eva_nombre = nombre
        evaluador.eva_correo = correo
        evaluador.eva_telefono = telefono
        evaluador.save()

        messages.success(request, 'Información actualizada correctamente.')
        return redirect('app_evaluador:detalle_evento_evaluador', cedula=evaluador.id, evento_id=request.POST.get('evento_id'))
    





def criterios_evaluacion(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    if request.method == 'POST':
        criterio = request.POST.get('criterio')
        porcentaje = request.POST.get('porcentaje')
        
        if criterio and porcentaje:
            try:
                peso = float(porcentaje)
                Criterios.objects.create(
                    cri_descripcion=criterio,
                    cri_peso=peso,
                    cri_evento_fk=evento
                )
                messages.success(request, "Criterio agregado correctamente.")
            except:
                messages.error(request, "Error al agregar el criterio.")
        else:
            messages.error(request, "Todos los campos son obligatorios.")
        return redirect('app_evaluador:criterios_evaluacion', evento_id=evento_id)

    criterios = Criterios.objects.filter(cri_evento_fk=evento)
    return render(request, 'app_evaluador/criterios_evaluacion.html', {
        'evento': evento,
        'criterios': criterios,
        'evaluador_id': request.session.get('evaluador_id'),
        'evaluador': request.session.get('evaluador_nombre'),
    })



    
def modificar_criterio(request, criterio_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            criterio = Criterios.objects.get(id=criterio_id)
            criterio.cri_descripcion = data.get('descripcion')
            criterio.cri_peso = data.get('porcentaje')
            criterio.save()
            return JsonResponse({'success': True})
        except Criterios.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Criterio no encontrado'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)



def eliminar_criterio(request, criterio_id):
    if request.method == 'POST':
        try:
            criterio = Criterios.objects.get(id=criterio_id)
            criterio.delete()
            return JsonResponse({'success': True})
        except Criterios.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No encontrado'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)



def tabla_calificaciones(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    subquery = (
        Calificaciones.objects
        .filter(cal_evento_fk=evento_id)
        .values('cal_participante_fk', 'cal_criterio_fk')
        .annotate(promedio_criterio=Avg('cal_valor'))
    )

    ranking_dict = {}
    for fila in subquery:
        criterio = Criterios.objects.filter(id=fila['cal_criterio_fk'], cri_evento_fk=evento_id).first()
        if criterio:
            participante_id = fila['cal_participante_fk']
            ponderado = fila['promedio_criterio'] * criterio.cri_peso / 100
            ranking_dict[participante_id] = ranking_dict.get(participante_id, 0) + ponderado

    ranking_ordenado = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    ranking = []
    for participante_id, promedio in ranking_ordenado:
        participante = Participantes.objects.get(id=participante_id)
        ranking.append({
            'id': participante.id,
            'nombre': participante.par_nombre,
            'promedio': round(promedio, 2)
        })

    return render(request, 'app_evaluador/posiciones.html', {
        'ranking': ranking,
        'evento': evento,
        'evaluador': request.session.get('eva_nombre'),
    })
    
def obtener_datos_preinscripcion(request, evento_id, evaluador_id):
    evaluador = EvaluadoresEventos.objects.filter(eva_eve_evento_fk = evento_id, eva_eve_evaluador_fk = evaluador_id).first()
    if evaluador:
        documento_url = evaluador.eva_eve_documentos.url if evaluador.eva_eve_documentos else None
        return JsonResponse({
            'nombre': evaluador.eva_eve_evaluador_fk.eva_nombre,
            'correo':  evaluador.eva_eve_evaluador_fk.eva_correo,
            'telefono': evaluador.eva_eve_evaluador_fk.eva_telefono,
            'documento': documento_url
        })
    else:
        return JsonResponse({'error': 'No encontrado'}, status=404)

def modificar_preinscripcion(request, evento_id, evaluador_id):
    evaluador = get_object_or_404(EvaluadoresEventos, eva_eve_evento_fk=evento_id, eva_eve_evaluador_fk=evaluador_id)

    if request.method == 'POST':
        # Accede al objeto Evaluador relacionado
        persona = evaluador.eva_eve_evaluador_fk

        # Modifica los campos del evaluador
        persona.eva_nombre = request.POST.get('nombre')
        persona.eva_correo = request.POST.get('correo')
        persona.eva_telefono = request.POST.get('telefono')
        persona.save()

        # Verifica y reemplaza el documento si se subió uno nuevo
        if 'documento' in request.FILES:
            # Elimina el documento anterior si existe
            if evaluador.eva_eve_documentos:
                documento_anterior_path = os.path.join(settings.MEDIA_ROOT, str(evaluador.eva_eve_documentos))
                if os.path.isfile(documento_anterior_path):
                    os.remove(documento_anterior_path)

            # Guarda el nuevo documento
            evaluador.eva_eve_documentos = request.FILES['documento']
            evaluador.save()

        print(f"Evaluador modificado: {persona.eva_nombre} (ID: {persona.id})")
        return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador_id)

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
def cancelar_inscripcion(request, evento_id, evaluador_id):
    if request.method == 'POST':
        relacion = get_object_or_404(
            EvaluadoresEventos,
            eva_eve_evento_fk=evento_id,
            eva_eve_evaluador_fk=evaluador_id
        )

        # Eliminar el documento asociado si existe
        if relacion.eva_eve_documentos:
            ruta_documento = relacion.eva_eve_documentos.path
            if os.path.exists(ruta_documento):
                os.remove(ruta_documento)
        
        relacion.delete()  # Elimina la inscripción
        return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador_id) 
    else:
        return redirect('app_evaluador:principal_evaluador', evaluador_id=evaluador_id)  # También redirige si no es POST