from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, Http404, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Avg, F, Sum, FloatField
from django.template.loader import render_to_string
from datetime import datetime
import os
from .utils import generar_pdf, generar_clave_acceso, obtener_ranking
from django.urls import reverse
from decimal import Decimal
import json
from weasyprint import HTML

from app_eventos.models import Eventos, EventosCategorias, ParticipantesEventos, AsistentesEventos, EvaluadoresEventos
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_administrador.models import Administradores
from app_criterios.models import Criterios
from app_evaluador.models import Calificaciones
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores

# Obtener áreas disponibles
def obtener_areas_eventos():
    return Areas.objects.all()

# Obtener categorías por área (AJAX)
@require_http_methods(["GET"])
def get_categorias(request, area_id):
    try:
        categorias = Categorias.objects.filter(cat_area_fk=area_id)
        resultado = [{'cat_codigo': c.id, 'cat_nombre': c.cat_nombre} for c in categorias]
        return JsonResponse(resultado, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener categorías: {str(e)}'}, status=500)

# Crear un nuevo evento
@csrf_exempt
@require_http_methods(["GET", "POST"])
def crear_evento(request):
    if request.method == 'POST':
        try:
            # Datos del formulario
            nombre = request.POST.get('nombre_evento')
            descripcion = request.POST.get('descripcion_evento')
            ciudad = request.POST.get('ciudad')
            lugar = request.POST.get('lugar')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            categoria = request.POST.get('categoria')
            inscripcion = request.POST.get('inscripcion')
            permitir_participantes = request.POST.get('permitir_participantes')

            # Aforo
            aforo = request.POST.get('cantidad_personas') if permitir_participantes == '1' else None

            # Archivos
            archivo_imagen = request.FILES.get('imagen_evento')
            archivo_programacion = request.FILES.get('documento_evento')

            # Obtener ID de administrador (puede estar vacío si no hay login aún)
            administrador_id = request.session.get('admin_cedula')

            # Crear evento
            evento = Eventos.objects.create(
                eve_nombre=nombre,
                eve_descripcion=descripcion,
                eve_ciudad=ciudad,
                eve_lugar=lugar,
                eve_fecha_inicio=datetime.strptime(fecha_inicio, "%Y-%m-%d").date(),
                eve_fecha_fin=datetime.strptime(fecha_fin, "%Y-%m-%d").date(),
                eve_estado="Pendiente",
                eve_imagen=archivo_imagen,
                eve_capacidad=int(aforo) if aforo else 0,
                eve_tienecosto=True if inscripcion == 'Si' else False,
                eve_programacion=archivo_programacion,
                eve_administrador_fk_id= 1 if administrador_id is None else administrador_id,
            )

            # Relación con categoría
            EventosCategorias.objects.create(
                eve_cat_evento_fk=evento,
                eve_cat_categoria_fk_id=categoria
            )

            messages.success(request, 'Evento creado exitosamente')
            return redirect('administrador:index_administrador')

        except Exception as e:
            print(f"Error al crear evento: {e}")
           

    # GET: mostrar formulario
    context = {
        'areas': obtener_areas_eventos(),
        'administrador': request.session.get('admin_nombre'),
    }
    return render(request, 'app_administrador/crearevento.html', context)

def inicio(request):
    # Obtener eventos (si tienes el modelo)
    eventos = Eventos.objects.filter(eve_administrador_fk = request.session.get('admin_cedula'))
    
    # Por ahora con datos hardcodeados como en tu ejemplo
    context = {
        'administrador': request.session.get('admin_nombre'),
        'eventos': eventos,
    }
    
    return render(request, 'app_administrador/admin.html', context)

@require_http_methods(["GET"])
def obtener_evento(request, evento_id):
    try:
        evento = Eventos.objects.get(id=evento_id)
    except Eventos.DoesNotExist:
        raise Http404("Evento no encontrado")

    # Obtener la categoría relacionada
    categoria_nombre = ""
    try:
        evento_categoria = EventosCategorias.objects.get(eve_cat_evento_fk=evento_id)
        categoria = Categorias.objects.get(id=evento_categoria.eve_cat_categoria_fk.id)
        categoria_nombre = categoria.cat_nombre
    except (EventosCategorias.DoesNotExist, Categorias.DoesNotExist):
        pass

    # Contar participantes y asistentes admitidos
    participantes = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento_id, par_eve_estado='Admitido').count()
    asistentes = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento_id, asi_eve_estado='Admitido').count()


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
        'eve_costo':'Con Pago' if evento.eve_tienecosto else 'Sin Pago',
        'eve_programacion': evento.eve_programacion.url if evento.eve_programacion else None,
        'eve_categoria': categoria_nombre,
        'cantidad_participantes': participantes,
        'cantidad_asistentes': asistentes,
    }

    return JsonResponse(datos_evento)

@csrf_exempt 
def eliminar_evento(request, evento_id):
    try:
        evento = Eventos.objects.get(id=evento_id)

        # Eliminar archivo de imagen si existe
        if evento.eve_imagen and evento.eve_imagen.name:
            if os.path.isfile(evento.eve_imagen.path):
                evento.eve_imagen.delete(save=False)

        # Eliminar archivo de programación si existe
        if evento.eve_programacion and evento.eve_programacion.name:
            if os.path.isfile(evento.eve_programacion.path):
                evento.eve_programacion.delete(save=False)

        # Finalmente eliminar el evento de la base de datos
        evento.delete()

        return JsonResponse({'mensaje': 'Evento eliminado correctamente'})

    except Eventos.DoesNotExist:
        return JsonResponse({'mensaje': 'Evento no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'mensaje': f'Error al eliminar el evento: {str(e)}'}, status=500)

def inicio_sesion_administrador(request):
    if request.method == "POST":
        cedula = request.POST.get("cedula")

        try:
            admin = Administradores.objects.get(adm_cedula=cedula)
            # Guardar en la sesión
            request.session['admin_cedula'] = admin.id
            request.session['admin_nombre'] = admin.adm_nombre

            # Redirigir pasando el nombre como parámetro de URL
            return redirect('administrador:index_administrador')
        except Administradores.DoesNotExist:
            messages.error(request, "Cédula no válida")

    return render(request, 'app_administrador/inicio_sesion.html')

@require_http_methods(["GET", "POST"])
def editar_evento(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    print(f"Evento a editar: {evento}")
    if request.method == 'POST':
        nombre = request.POST.get('nombre_evento')
        descripcion = request.POST.get('descripcion_evento')
        ciudad = request.POST.get('ciudad')
        lugar = request.POST.get('lugar')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        categoria = request.POST.get('categoria')
        inscripcion = request.POST.get('inscripcion')
        estado = request.POST.get('estado_evento')
        aforo = request.POST.get('cantidad_personas') or None
        aforo = int(aforo) if aforo else None
        
        # Archivos
        imagen = request.FILES.get('imagen_evento')
        documento = request.FILES.get('documento_evento')

        if imagen:
            # Eliminar archivo anterior si existe
            if evento.eve_imagen and evento.eve_imagen.name:
                if os.path.isfile(evento.eve_imagen.path):
                    evento.eve_imagen.delete(save=False)
            evento.eve_imagen = imagen

        if documento:
            # Eliminar archivo anterior si existe
            if evento.eve_programacion and evento.eve_programacion.name:
                if os.path.isfile(evento.eve_programacion.path):
                    evento.eve_programacion.delete(save=False)
            evento.eve_programacion = documento

        # Campos normales
        evento.eve_nombre = nombre
        evento.eve_descripcion = descripcion
        evento.eve_ciudad = ciudad
        evento.eve_lugar = lugar
        evento.eve_fecha_inicio = parse_datetime(fecha_inicio)
        evento.eve_fecha_fin = parse_datetime(fecha_fin)
        evento.eve_capacidad = aforo if aforo is not None else 0
        evento.eve_tienecosto = True if inscripcion == 'Si' else False
        evento.eve_estado = estado

        evento.save()

        # Actualizar categoría del evento
        evento_categoria = EventosCategorias.objects.filter( eve_cat_evento_fk=evento_id).first()
        if evento_categoria:
            evento_categoria.categoria_id = categoria
            evento_categoria.save()
        return redirect('administrador:index_administrador')  # Asegúrate de tener esta URL nombrada

    else:
        evento_categoria = EventosCategorias.objects.filter(eve_cat_evento_fk=evento).first()
        categoria_evento = evento_categoria.eve_cat_categoria_fk if evento_categoria else None
        area_categoria = categoria_evento.cat_area_fk if categoria_evento else None  # Si existe ese campo


        contexto = {
            'evento': evento,
            'categoria_seleccionada': categoria_evento,
            'area_seleccionada': area_categoria,
            'areas': obtener_areas_eventos(),
            'categorias': Categorias.objects.all(),
            'administrador': request.session.get('admin_nombre'),
        }

        return render(request, 'app_administrador/modificarInformacion.html', contexto)
    
@require_http_methods(["GET", "POST"])
def ver_participantes(request: HttpRequest ,evento_id):
    estado = request.GET.get('estado')

    # Filtrar participantes_eventos según evento y estado
    participantes_eventos = ParticipantesEventos.objects.select_related('par_eve_participante_fk').filter(
       par_eve_evento_fk=evento_id,
        par_eve_estado=estado
    )
    evento = get_object_or_404(Eventos, id=evento_id)
    # Construir lista de diccionarios con datos para la plantilla
    participantes = []
    for pe in participantes_eventos:
        p = pe.par_eve_participante_fk
        participantes.append({
            'par_id': p.id,
            'par_cedula': p.par_cedula,
            'par_nombre': p.par_nombre,
            'par_correo': p.par_correo,
            'par_telefono': p.par_telefono,
            'documentos': pe.par_eve_documentos,
            'estado': pe.par_eve_estado,
            'hora_inscripcion': pe.par_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if pe.par_eve_fecha_hora else None,
        })


    return render(request, 'app_administrador/ver_participantes.html', {
        'participantes': participantes,
        'evento_id': evento_id,
        'evento_nombre': evento.eve_nombre,
    })

@csrf_exempt 
def actualizar_estado(request, participante_id, nuevo_estado):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')

        if not evento_id:
            return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

        # Generar PDF y clave de acceso
        if nuevo_estado == 'Admitido':
            qr_participante = generar_pdf(participante_id, "Participante", evento_id, tipo="participante")
            clave_acceso = generar_clave_acceso()
        else:
            qr_participante = None
            clave_acceso = None
        # Buscar el participante_evento
        try:
            participante_evento = ParticipantesEventos.objects.get(
                par_eve_participante_fk=participante_id,
                par_eve_evento_fk=evento_id
            )
        except ParticipantesEventos.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Participante no encontrado en el evento'}, status=404)

        # Actualizar los valores
        participante_evento.par_eve_estado = nuevo_estado
        participante_evento.par_eve_qr = qr_participante
        participante_evento.par_eve_clave = clave_acceso if nuevo_estado == 'Admitido' else 0
        participante_evento.save()
        url = reverse('administrador:ver_participantes', kwargs={'evento_id': evento_id})
        return redirect(f'{url}?estado={nuevo_estado}')

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def ver_asistentes(request: HttpRequest, evento_id):
    estado = request.GET.get('estado')

    # Obtener los asistentes del evento utilizando el ORM de Django
    asistentes_evento = AsistentesEventos.objects.select_related('asi_eve_asistente_fk').filter(
        asi_eve_evento_fk=evento_id,
        asi_eve_estado=estado)
    
    evento = get_object_or_404(Eventos, id=evento_id)

    # Preparar los datos
    asistentes_data = []
    for ae in asistentes_evento:
        a = ae.asi_eve_asistente_fk
        asistentes_data.append({
            'asi_id': a.id,
            'asi_nombre': a.asi_nombre,
            'asi_correo': a.asi_correo,
            'asi_telefono': a.asi_telefono,
            'documentos': ae.asi_eve_soporte.url if ae.asi_eve_soporte else None,
            'estado': ae.asi_eve_estado,
            'hora_inscripcion': ae.asi_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if ae.asi_eve_fecha_hora else None,
        })

    return render(request, 'app_administrador/ver_asistentes.html', {
        'asistentes': asistentes_data,
        'evento_id': evento_id,
        'evento_nombre': evento.eve_nombre,
    })
    
@csrf_exempt
def actualizar_estado_asistente(request, asistente_id, nuevo_estado):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')

        if not evento_id:
            return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

        # Generar PDF y clave de acceso
        if nuevo_estado == 'Admitido':
            qr_participante = generar_pdf(asistente_id, "Asistente", evento_id, tipo="asistente")
            clave_acceso = generar_clave_acceso()
        else:
            qr_participante = None
            clave_acceso = None

        # Buscar el asistente_evento
        asistente_evento = AsistentesEventos.objects.filter(
            asi_eve_asistente_fk=asistente_id,
            asi_eve_evento_fk=evento_id
        ).first()

        if not asistente_evento:
            return JsonResponse({'status': 'error', 'message': 'Asistente no encontrado en el evento'}, status=404)

        # Actualizar los valores
        asistente_evento.asi_eve_estado = nuevo_estado
        asistente_evento.asi_eve_qr = qr_participante
        asistente_evento.asi_eve_clave = clave_acceso if nuevo_estado == 'Admitido' else 0
        asistente_evento.save()

        url = reverse('administrador:ver_asistentes', kwargs={'evento_id': evento_id})
        return redirect(f'{url}?estado={nuevo_estado}')

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@csrf_exempt
def criterios_evaluacion(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    
    if request.method == 'POST':
        criterios = request.POST.getlist('criterio[]')
        porcentajes = request.POST.getlist('porcentaje[]')

        try:
            porcentajes_float = [Decimal(p) for p in porcentajes]
        except ValueError:
            messages.error(request, "Porcentajes inválidos.")
            return redirect('administrador:criterios_evaluacion', evento_id=evento_id)

        suma_nuevos = sum(porcentajes_float)

        criterios_existentes = Criterios.objects.filter(cri_evento_fk=evento_id)
        suma_existente = sum(c.cri_peso for c in criterios_existentes)

        # suma_existente ya es una suma de Decimals
        if suma_existente + suma_nuevos > Decimal('100'):
            messages.error(request, "La suma de los porcentajes no puede superar el 100%.")
            return redirect('administrador:criterios_evaluacion', evento_id=evento_id)
        
        for desc, porc in zip(criterios, porcentajes_float):
            Criterios.objects.create( cri_descripcion=desc, cri_peso=porc,  cri_evento_fk=evento)

        messages.success(request, "Criterio(s) agregado(s) correctamente.")
        return redirect('administrador:criterios_evaluacion', evento_id=evento_id)


    context = {
        'evento': evento,
        'administrador': request.session.get('admin_nombre'),
        'criterios': Criterios.objects.filter(cri_evento_fk=evento_id),
    }
    
    return render(request, 'app_administrador/criterios_evaluacion.html', context)

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

    # Subconsulta: promedio por criterio y participante
    subquery = (
        Calificaciones.objects
        .values('clas_participante_fk', 'cal_criterio_fk')
        .annotate(promedio_criterio=Avg('cal_valor'))
    )

    # Diccionario temporal para almacenar acumulados
    ranking_dict = {}

    for row in subquery:
        criterio = Criterios.objects.filter(id=row['cal_criterio_fk'], cri_evento_fk=evento_id).first()
        if criterio:
            participante_id = row['clas_participante_fk']
            ponderado = row['promedio_criterio'] * criterio.cri_peso / 100

            if participante_id not in ranking_dict:
                ranking_dict[participante_id] = 0
            ranking_dict[participante_id] += ponderado

    # Ordenar por promedio ponderado descendente
    ranking_ordenado = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    # Construir lista para el template
    ranking = []
    for participante_id, promedio in ranking_ordenado:
        participante = Participantes.objects.get(id=participante_id)
        ranking.append({
            'id': participante.id,
            'nombre': participante.par_nombre,
            'promedio': round(promedio, 2)
        })

    return render(request, 'app_administrador/posiciones.html', {
        'ranking': ranking,
        'evento': evento,
        'administrador': request.session.get('admin_nombre'),
    })
    
def descargar_ranking_pdf(request, evento_id):
    evento = Eventos.objects.get(id=evento_id)
    ranking = obtener_ranking(evento_id)  # debe devolver lista de diccionarios con nombre y promedio

    html_string = render_to_string('app_administrador/ranking_pdf.html', {
        'evento': evento,
        'ranking': ranking,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="ranking_evento_{evento_id}.pdf"'

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response



def detalles_calificaciones(request, evento_id, participante_id):
    participante = get_object_or_404(Participantes, id=participante_id)
    evento = get_object_or_404(Eventos, id=evento_id)

    # Traer todas las calificaciones del participante en ese evento
    calificaciones = Calificaciones.objects.filter(
        clas_participante_fk=participante,
        cal_criterio_fk__cri_evento_fk=evento
    ).select_related('cal_evaluador_fk', 'cal_criterio_fk')

    # Agrupar por evaluador
    evaluadores_data = {}
    for cal in calificaciones:
        evaluador = cal.cal_evaluador_fk
        criterio = cal.cal_criterio_fk
        if evaluador.id not in evaluadores_data:
            evaluadores_data[evaluador.id] = {
                'evaluador': evaluador,
                'calificaciones': [],
                'puntaje_total': 0.0,
            }

        # Calcular puntaje ponderado para este criterio
        ponderado = float(cal.cal_valor) * float(criterio.cri_peso) / 100

        evaluadores_data[evaluador.id]['calificaciones'].append({
            'criterio': criterio.cri_descripcion,
            'peso': criterio.cri_peso,
            'valor': cal.cal_valor,
            'ponderado': round(ponderado, 2),
        })

        # Sumar al total ponderado de ese evaluador
        evaluadores_data[evaluador.id]['puntaje_total'] += ponderado

    # Redondear puntajes totales
    for data in evaluadores_data.values():
        data['puntaje_total'] = round(data['puntaje_total'], 2)

    return render(request, 'app_administrador/detalle_calificaciones.html', {
        'participante': participante,
        'evento': evento,
        'evaluadores_data': evaluadores_data.values(),
        'administrador': request.session.get('admin_nombre'),
    })


def detalle_calificacion(request, participante_id, evaluador_id, evento_id):
    participante = get_object_or_404(Participantes, id=participante_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

    # Obtener todas las calificaciones de ese evaluador a ese participante
    calificaciones = Calificaciones.objects.filter(
        clas_participante_fk=participante,
        cal_evaluador_fk=evaluador
    ).select_related('cal_criterio_fk')

    calificaciones_info = []
    puntaje_total = 0

    for cal in calificaciones:
        criterio = cal.cal_criterio_fk
        ponderado = float(cal.cal_valor) * float(criterio.cri_peso) / 100
        puntaje_total += ponderado
        calificaciones_info.append({
            'criterio': criterio.cri_descripcion,
            'peso': float(criterio.cri_peso),
            'valor': float(cal.cal_valor),
            'ponderado': round(ponderado, 2)
        })

    return render(request, 'app_administrador/detalle_calificacion_participante.html', {
        'participante': participante,
        'evaluador': evaluador,
        'calificaciones_info': calificaciones_info,
        'puntaje_total': round(puntaje_total, 2),
        'administrador': request.session.get('admin_nombre'),
        'evento': get_object_or_404(Eventos, id=evento_id)
    })

def ver_evaluadores(request: HttpRequest, evento_id):
    estado = request.GET.get('estado')

    # Obtener los asistentes del evento utilizando el ORM de Django
    evaluadores_evento = EvaluadoresEventos.objects.select_related('eva_eve_evaluador_fk').filter(
        eva_eve_evento_fk=evento_id,
        eva_estado=estado)
    
    evento = get_object_or_404(Eventos, id=evento_id)

    # Preparar los datos
    evaluadores_data = []
    for ee in evaluadores_evento:
        e = ee.eva_eve_evaluador_fk
        evaluadores_data.append({
            'asi_id': e.id,
            'asi_nombre': e.eva_nombre,
            'asi_correo': e.eva_correo,
            'asi_telefono': e.eva_telefono,
            'estado': ee.eva_estado,
            'hora_inscripcion': ee.eva_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if ee.eva_eve_fecha_hora else None,
        })

    return render(request, 'app_administrador/ver_evaluadores.html', {
        'evaluadores': evaluadores_data,
        'evento_id': evento_id,
        'evento_nombre': evento.eve_nombre,
    })

@csrf_exempt
def actualizar_estado_evaluador(request, evaluador_id, nuevo_estado):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')

        if not evento_id:
            return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

        # Generar PDF y clave de acceso
        if nuevo_estado == 'Admitido':
            qr_evaluador = generar_pdf(evaluador_id, "Evaluador", evento_id, tipo="evaluador")
        else:
            qr_evaluador = None
        # Buscar el participante_evento
        try:
            evaluador_evento = EvaluadoresEventos.objects.get(
                eva_eve_evaluador_fk=evaluador_id,
                eva_eve_evento_fk=evento_id
            )
        except EvaluadoresEventos.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Asistente no encontrado en el evento'}, status=404)

        # Actualizar los valores
        evaluador_evento.eva_estado = nuevo_estado
        evaluador_evento.eva_eve_qr = qr_evaluador
        evaluador_evento.save()
        print("Evaluador actualizado con estado:", nuevo_estado)
        url = reverse('administrador:ver_asistentes', kwargs={'evento_id': evento_id})
        return redirect(f'{url}?estado={nuevo_estado}')

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)