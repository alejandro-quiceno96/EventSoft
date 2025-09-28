from django.http import JsonResponse
from app_criterios.models import Criterios
from django.shortcuts import render, get_object_or_404,  redirect
from app_participante.models import Participantes
from .models import Evaluadores
from django.contrib import messages
from app_eventos.models import ParticipantesEventos, EvaluadoresEventos,Eventos, Proyecto
from .models import Calificaciones, EvaluadorProyecto
from django.db.models import Avg,F
from django.urls import reverse
from app_eventos.models import EventosCategorias
import json
from django.http import HttpResponse
from weasyprint import HTML
from app_categorias.models import Categorias
from django.http import JsonResponse, Http404, HttpResponse
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum


@login_required(login_url='login')
def principal_evaluador(request):
    try:
        evaluador = get_object_or_404(Evaluadores, usuario = request.user)
        # Traemos las relaciones EvaluadoresEventos para ese evaluador, incluyendo los eventos relacionados
        evaluadores_eventos = EvaluadoresEventos.objects.filter(eva_eve_evaluador_fk=evaluador).select_related('eva_eve_evento_fk')
        request.session['evaluador_id'] = evaluador.id
        request.session['evaluador_nombre'] = evaluador.usuario.username
        
        ahora = timezone.localdate()
        print(f"Hora actual: {ahora}")
        for relacion in evaluadores_eventos:
            evento = relacion.eva_eve_evento_fk
            if evento.eve_fecha_inicio <= ahora <= evento.eve_fecha_fin:
                relacion.estado_evento = "en_curso"
                print(f"Evento {evento.eve_nombre} está en curso.")
            elif ahora < evento.eve_fecha_inicio:
                relacion.estado_evento = "no_iniciado"
                print(f"Evento {evento.eve_nombre} no ha comenzado aún.")
            else:
                relacion.estado_evento = "terminado"
                print(f"Evento {evento.eve_nombre} ha terminado.")
        
        # Pasamos ese queryset al contexto
        return render(request, 'app_evaluador/inicio_evaluador.html', {
            'evaluador': evaluador,
            'evaluador_id': request.user.id,
            'eventos': evaluadores_eventos
        })
    except Exception as e:
        return render(request, 'app_evaluador/inicio_evaluador.html', {
            'evaluador': request.user.username,

            'evaluador_id': request.user.id,
            'eventos':  []
        })




@login_required(login_url='login')
def ver_participantes(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    evaluador = get_object_or_404(Evaluadores, usuario=request.user)
    proyectos_calificar = EvaluadorProyecto.objects.filter(eva_pro_evaluador_fk=evaluador)
    evaluadores_eventos = EvaluadoresEventos.objects.filter(eva_eve_evaluador_fk=evaluador).select_related('eva_eve_evento_fk')

    proyectos = []
    for proyecto in proyectos_calificar:
        # Todos los expositores del proyecto
        expositores = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento,
            par_eve_proyecto=proyecto.eva_pro_proyecto_fk
        )

        # Lista de nombres de los expositores
        nombres_expositores = [
            f"{exp.par_eve_participante_fk.usuario.first_name} {exp.par_eve_participante_fk.usuario.last_name}"
            for exp in expositores
        ]

        proyectos.append({
            "expositores": nombres_expositores,
            "pro_nombre": proyecto.eva_pro_proyecto_fk.pro_nombre,
            "pro_codigo": proyecto.eva_pro_proyecto_fk.pro_codigo,
            "pro_id": proyecto.eva_pro_proyecto_fk.id,
        })
    
    # Guardamos el ID en sesión
    request.session['evaluador_id'] = evaluador.id
    request.session['evaluador_nombre'] = evaluador.usuario.username

    # Participantes evaluados por este evaluador
    calificados_ids = Calificaciones.objects.filter(
        cal_evaluador_fk_id=evaluador.id,
        cal_criterio_fk__cri_evento_fk=evento
    ).values_list('clas_proyecto_fk_id', flat=True).distinct()

    evaluados_dict = {pid: True for pid in calificados_ids}
    

    # Ranking
    ranking = []
    proyectos_ranking =  Proyecto.objects.filter(pro_evento_fk=evento).order_by('-pro_calificación_final')
    for proyecto in proyectos_ranking:
        # Todos los expositores del proyecto
        expositores = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento,
            par_eve_proyecto=proyecto
        )

        # Lista de nombres de los expositores
        nombres_expositores = [
            f"{exp.par_eve_participante_fk.usuario.first_name} {exp.par_eve_participante_fk.usuario.last_name}"
            for exp in expositores
        ]

        ranking.append({
            "expositores": nombres_expositores,
            "pro_nombre": proyecto.pro_nombre,
            "pro_codigo": proyecto.pro_codigo,
            "pro_calificacion_final": proyecto.pro_calificación_final if proyecto.pro_calificación_final is not None else 0,
        })

    context = {
        'evento': evento,
        'proyectos': proyectos,
        'evaluador_id': evaluador.id,
        'ranking': ranking,
        'evaluados_dict': evaluados_dict,
    }

    return render(request, 'app_evaluador/participantes_evento.html', context)

def api_calificaciones(request, evento_id, proyecto_id, evaluador_id):
    calificaciones = Calificaciones.objects.filter(
        cal_evaluador_fk=evaluador_id,
        clas_proyecto_fk=proyecto_id,
        cal_criterio_fk__cri_evento_fk__id=evento_id
    ).select_related('cal_criterio_fk')

    data = {
        'calificaciones': [
            {
                'criterio': cal.cal_criterio_fk.cri_descripcion, 
                'peso': cal.cal_criterio_fk.cri_peso,
                'puntaje': cal.cal_valor,
                'comentario': cal.cal_comentario,
            }
            for cal in calificaciones
        ]
    }
    return JsonResponse(data, status=200)

@login_required(login_url='login')
def evaluar_participante(request, evento_id, proyecto_id, evaluador_id):
    # --- Obtener instancias ---
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    evento = get_object_or_404(Eventos, id=evento_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    criterios = Criterios.objects.filter(cri_evento_fk=evento)

    if request.method == 'POST':
        nuevas_calificaciones = []

        # --- Recorremos criterios y guardamos calificaciones ---
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
                            clas_proyecto_fk=proyecto,   # Proyecto evaluado
                            cal_evaluador_fk=evaluador
                        )
                        nuevas_calificaciones.append(calificacion)
                except ValueError:
                    continue

        # Guardar en lote
        if nuevas_calificaciones:
            Calificaciones.objects.bulk_create(nuevas_calificaciones)

        # --- Cálculo del promedio ponderado ---
        subquery = (
            Calificaciones.objects
            .filter(clas_proyecto_fk=proyecto)
            .values('clas_proyecto_fk', 'cal_criterio_fk')
            .annotate(promedio_criterio=Avg('cal_valor'))
        )

        promedio_final = 0
        for row in subquery:
            criterio = Criterios.objects.filter(
                id=row['cal_criterio_fk'],
                cri_evento_fk=evento
            ).first()

            if criterio:
                ponderado = row['promedio_criterio'] * (criterio.cri_peso / 100)
                promedio_final += ponderado

        promedio_final = round(promedio_final, 2)

        # --- Actualizar TODOS los expositores de ese proyecto ---
        expositores = ParticipantesEventos.objects.filter(
            par_eve_proyecto=proyecto,
            par_eve_evento_fk=evento
        )

        for expositor in expositores:
            expositor.par_eve_calificacion_final = promedio_final
            expositor.save()

        # --- También actualizar el proyecto ---
        proyecto.pro_calificación_final = promedio_final
        proyecto.save()

        messages.success(request, "✅ Evaluación guardada correctamente.")
        return redirect(
            reverse('app_evaluador:ver_participantes', kwargs={'evento_id': evento.id}) + '?calificacion=realizada'
        )

    # --- Contexto para renderizar ---
    context = {
        'proyecto': proyecto,
        'evento': evento,
        'evaluador': evaluador,
        'evaluador_nombre': request.session.get('evaluador_nombre'),
        'criterios': criterios
    }
    return render(request, 'app_evaluador/evaluar_participante.html', context)




@login_required(login_url='login') 
def obtener_calificaciones(request, evento_id, participante_id, evaluador_id):
    calificaciones = Calificaciones.objects.filter(
        cal_criterio_fk__cri_evento_fk__id=evento_id,
        clas_proyecto_fk__id=participante_id,
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

 
login_required(login_url='login')
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
        'evaluador': evaluador 
    }

    return JsonResponse(datos_evento)


def generar_reporte_evaluador(request, cedula):
    """Generar reporte PDF del evaluador"""
    try:
        evaluador = get_object_or_404(Evaluadores, eva_cedula=cedula)
        
        # CORRECCIÓN: Usar select_related de forma segura
        calificaciones = Calificaciones.objects.filter(
            cal_evaluador_fk=evaluador
        ).select_related('clas_proyecto_fk')
        
        # Obtener eventos únicos donde ha evaluado
        eventos_evaluados = set()
        for cal in calificaciones:
            if hasattr(cal, 'clas_proyecto_fk') and cal.clas_proyecto_fk:
                # Ajustar según la estructura real de tu modelo
                if hasattr(cal.clas_proyecto_fk, 'par_eve_evento_fk'):
                    eventos_evaluados.add(cal.clas_proyecto_fk.par_eve_evento_fk)
                elif hasattr(cal.clas_proyecto_fk, 'evento'):
                    eventos_evaluados.add(cal.clas_proyecto_fk.evento)
        
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
            if hasattr(cal, 'clas_proyecto_fk') and cal.clas_proyecto_fk:
                # Ajustar según la estructura real de tu modelo
                if hasattr(cal.clas_proyecto_fk, 'par_eve_evento_fk'):
                    if cal.clas_proyecto_fk.par_eve_evento_fk == evento:
                        participantes_evaluados.add(cal.clas_proyecto_fk.id)
        
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
    proyectos_eventos = EvaluadorProyecto.objects.filter(eva_pro_evaluador_fk=cedula)
    
    proyectos = []
    for proyecto in proyectos_eventos:
        # Todos los expositores del proyecto
        expositores = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento,
            par_eve_proyecto=proyecto.eva_pro_proyecto_fk
        )

        # Lista de nombres de los expositores
        nombres_expositores = [
            f"{exp.par_eve_participante_fk.usuario.first_name} {exp.par_eve_participante_fk.usuario.last_name}"
            for exp in expositores
        ]

        proyectos.append({
            "pro_nombre": proyecto.eva_pro_proyecto_fk.pro_nombre,
            "pro_documentos": proyecto.eva_pro_proyecto_fk.pro_documentos,
            "expositores": nombres_expositores,  # 👈 aquí guardas los nombres
        })
        


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
    print(proyectos)

    return render(request, 'app_evaluador/detalle_evento.html', {
    'evento': datos_evento,
    'evaluador': evaluador,
    'proyectos': proyectos,
    'evento_obj': evento, 
})

def inicio_evaluador(request):
    return render(request, 'app_evaluador/inicio_evaluador.html')


def subir_info_tecnica(request, pk):
    print("Archivos recibidos:", request.FILES)

    if request.method == 'POST':
        evento = get_object_or_404(Eventos, pk=pk)
        evaluador_id = request.POST.get('cedula')

        if not evaluador_id:
            return JsonResponse({'success': False, 'message': 'No se pudo identificar al evaluador.'})

        try:
            evaluador = Evaluadores.objects.get(id=evaluador_id)
        except Evaluadores.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Evaluador no encontrado.'})

        if 'eve_informacion_tecnica' in request.FILES:
            evento.eve_informacion_tecnica = request.FILES['eve_informacion_tecnica']
            evento.save()
            return redirect('app_evaluador:detalle_evento_evaluador', evento_id=evento.id, cedula=evaluador.id)
        else:
            return JsonResponse({'success': False, 'message': 'No se encontró el archivo a subir.'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})
    

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
    total_peso = sum(int(c.cri_peso) for c in criterios) if criterios else 0
    return render(request, 'app_evaluador/criterios_evaluacion.html', {
        'evento': evento,
        'total_peso': total_peso,
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
            'documento': documento_url
        })
    else:
        return JsonResponse({'error': 'No encontrado'}, status=404)

def modificar_preinscripcion(request, evento_id, evaluador_id):
    evaluador = get_object_or_404(EvaluadoresEventos, eva_eve_evento_fk=evento_id, eva_eve_evaluador_fk=evaluador_id)

    if request.method == 'POST':

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
        return redirect('app_evaluador:principal_evaluador')

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
def cancelar_inscripcion(request, evento_id, evaluador_id):
    if request.method == 'POST':
        relacion = get_object_or_404(
            EvaluadoresEventos,
            eva_eve_evento_fk=evento_id,
            eva_eve_evaluador_fk=evaluador_id
        )
        # Obtener el participante
        evaluador = Evaluadores.objects.get(id=evaluador_id)
            
        # Verificar cuántas inscripciones tiene este participante ANTES de eliminar
        total_inscripciones = EvaluadoresEventos.objects.filter(
            eva_eve_evaluador_fk= evaluador_id
        ).count()

        # Eliminar el documento asociado si existe
        if relacion.eva_eve_documentos:
            ruta_documento = relacion.eva_eve_documentos.path
            if os.path.exists(ruta_documento):
                os.remove(ruta_documento)
                
        
        
        relacion.delete()  # Elimina la inscripción
        
        # Si era la única inscripción, eliminar el participante
        if total_inscripciones == 1:
            evaluador.delete()
        return redirect('app_evaluador:principal_evaluador') 
    else:
        return redirect('app_evaluador:principal_evaluador')  # También redirige si no es POST
    
login_required(login_url='login')  # Protege la vista para usuarios logueados
def editar_perfil(request):
    user = request.user  # Es instancia de tu modelo Usuario

    if request.method == 'POST':
        # Campos básicos
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.username = request.POST.get('username', '')
        user.email = request.POST.get('email', '')

        # Campos adicionales de tu modelo
        user.segundo_nombre = request.POST.get('segundo_nombre', '')
        user.segundo_apellido = request.POST.get('segundo_apellido', '')
        user.telefono = request.POST.get('telefono', '')
        user.fecha_nacimiento = request.POST.get('fecha_nacimiento', '')

        # Manejo de contraseña si el usuario desea cambiarla
        if request.POST.get('current_password'):
            current_password = request.POST.get('current_password')
            if user.check_password(current_password):
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                if new_password == confirm_password and new_password != '':
                    user.set_password(new_password)
                    update_session_auth_hash(request, user)  # Mantener sesión
                    messages.success(request, 'Contraseña actualizada correctamente.')
                else:
                    messages.error(request, 'Las contraseñas no coinciden o están vacías.')
                    return redirect('app_evaluador:principal_evaluador')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('app_evaluador:principal_evaluador')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('app_evaluador:principal_evaluador')  # Redirige a la página de inicio del visitante

    return redirect('app_evaluador:principal_evaluador')  # Redirige a la página de inicio si no es POST