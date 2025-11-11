from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, Http404, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.template.loader import render_to_string
from django.contrib.auth import update_session_auth_hash
from datetime import datetime
import os
from django.views.decorators.http import require_POST
from .utils import generar_pdf, generar_clave_acceso, obtener_ranking, generar_certificados, generar_reconocmiento, generar_certificados_expositores
from django.urls import reverse
from decimal import Decimal
import json
from django.utils.dateparse import parse_date
from weasyprint import HTML
from django.core.mail import EmailMessage
from django.conf import settings
from app_asistente.models import Asistentes
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
import locale
from django.utils.timezone import now

from datetime import date

from app_eventos.models import Eventos, EventosCategorias, ParticipantesEventos, AsistentesEventos, EvaluadoresEventos, Proyecto
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_administrador.models import Administradores
from app_criterios.models import Criterios
from app_evaluador.models import Calificaciones, EvaluadorProyecto
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores
from app_certificados.models import Certificado

from app_super_admin.models import SuperAdministradores


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
@login_required(login_url='login')  # Protege la vista para usuarios logueados
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

            aforo = request.POST.get('cantidad_personas') if permitir_participantes == '1' else None
            archivo_imagen = request.FILES.get('imagen_evento')
            archivo_programacion = request.FILES.get('documento_evento')

            administrador = Administradores.objects.get(usuario=request.user)

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
                eve_administrador_fk_id=administrador.id,
            )

            EventosCategorias.objects.create(
                eve_cat_evento_fk=evento,
                eve_cat_categoria_fk_id=categoria
            )
            
            administrador.num_eventos -= 1
            administrador.save()

            # 🟩 ENVIAR CORREO A SUPERADMINISTRADORES
            superadmins =   SuperAdministradores.objects.select_related('usuario').all()

            for superadmin in superadmins:
                mensaje_html = render_to_string('app_administrador/correos/notificacion_evento_creado.html', {
                "nombre": evento.eve_nombre,
                "descripcion": evento.eve_descripcion,
                "ciudad": evento.eve_ciudad,
                "lugar": evento.eve_lugar,
                "fecha_inicio": evento.eve_fecha_inicio,
                "fecha_fin": evento.eve_fecha_fin,
            })


                email = EmailMultiAlternatives(
                    f"Nuevo evento creado: {evento.eve_nombre}",
                    "",  # texto plano opcional
                    settings.DEFAULT_FROM_EMAIL,
                    [superadmin.usuario.email]
                )
                email.attach_alternative(mensaje_html, "text/html")
                email.send(fail_silently=False)

            return redirect(reverse('administrador:crear_evento') + '?revision=evento')

        except Exception as e:
            print(f"Error al crear evento: {e}")

    context = {
        'areas': obtener_areas_eventos(),
        'administrador': request.session.get('admin_nombre'),
    }
    return render(request, 'app_administrador/crearevento.html', context)

    

def subir_info_tecnica(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    if request.method == 'POST' and request.FILES.get('eve_informacion_tecnica'):
        archivo = request.FILES['eve_informacion_tecnica']
        evento.eve_informacion_tecnica = archivo
        evento.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)

@login_required(login_url='login')
def inicio(request):
    administrador = Administradores.objects.get(usuario_id=request.user.id)
    eventos = Eventos.objects.filter(eve_administrador_fk=administrador.id)
    
    # Agregar los totales directamente a cada evento
    for evento in eventos:
        evento.total_participantes = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento.id).count()
        evento.total_asistentes = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento.id).count()
        evento.total_evaluadores = EvaluadoresEventos.objects.filter(eva_eve_evento_fk=evento.id).count()
        evento.total_inscritos = evento.total_participantes + evento.total_asistentes + evento.total_evaluadores

    context = {
        'administrador': administrador,
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
    certificado_existe = Certificado.objects.filter(evento_fk=evento_id).first()
    if certificado_existe:
        certificado = True
    else:
        certificado = False

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
        'memorias': evento.eve_memorias if evento.eve_memorias else False,
        'certificado': certificado,
        'ficha_tecnica': evento.eve_informacion_tecnica.url if evento.eve_informacion_tecnica else False,
        'inscripcion_expositor': evento.eve_habilitar_participantes,
        'inscripcion_evaluador': evento.eve_habilitar_evaluadores,
    }

    return JsonResponse(datos_evento)

@csrf_exempt
@login_required(login_url='login')
def eliminar_evento(request, evento_id):
    # 🚫 Validar que el método sea POST
    if request.method != 'POST':
        return JsonResponse({'mensaje': 'Método no permitido'}, status=405)

    try:
        evento = Eventos.objects.get(id=evento_id)

        # 🔹 Validar que el evento no esté cerrado
        if evento.eve_estado == 'Cerrado':
            return JsonResponse(
                {'mensaje': 'No se puede eliminar un evento cerrado.'},
                status=403
            )

        # 🔹 Eliminar imagen asociada
        if evento.eve_imagen and evento.eve_imagen.name:
            if os.path.isfile(evento.eve_imagen.path):
                evento.eve_imagen.delete(save=False)

        # 🔹 Eliminar archivo de programación asociado
        if evento.eve_programacion and evento.eve_programacion.name:
            if os.path.isfile(evento.eve_programacion.path):
                evento.eve_programacion.delete(save=False)

        # 🔹 Eliminar el evento
        evento.delete()

        return JsonResponse({'mensaje': 'Evento eliminado correctamente'}, status=200)

    except Eventos.DoesNotExist:
        return JsonResponse({'mensaje': 'Evento no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'mensaje': f'Error al eliminar el evento: {str(e)}'}, status=500)

    
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def editar_evento(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    # Bloquear si el evento está cerrado
    if evento.eve_estado.lower() == "cerrado":
        messages.error(request, "No se puede editar un evento cerrado.")
        return redirect('administrador:index_administrador')

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
            if evento.eve_imagen and evento.eve_imagen.name:
                if os.path.isfile(evento.eve_imagen.path):
                    evento.eve_imagen.delete(save=False)
            evento.eve_imagen = imagen

        if documento:
            if evento.eve_programacion and evento.eve_programacion.name:
                if os.path.isfile(evento.eve_programacion.path):
                    evento.eve_programacion.delete(save=False)
            evento.eve_programacion = documento

        # Validar fechas
        fecha_inicio_obj = parse_date(fecha_inicio)
        fecha_fin_obj = parse_date(fecha_fin)

        if not fecha_inicio_obj or not fecha_fin_obj:
            messages.error(request, "Debe ingresar fechas válidas.")
            return redirect('administrador:index_administrador')

        if fecha_fin_obj < fecha_inicio_obj:
            messages.error(request, "La fecha fin no puede ser anterior a la fecha inicio.")
            return redirect('administrador:index_administrador')

        # Guardar campos
        evento.eve_nombre = nombre
        evento.eve_descripcion = descripcion
        evento.eve_ciudad = ciudad
        evento.eve_lugar = lugar
        evento.eve_fecha_inicio = fecha_inicio_obj
        evento.eve_fecha_fin = fecha_fin_obj
        evento.eve_capacidad = aforo if aforo is not None else 0
        evento.eve_tienecosto = True if inscripcion == 'Si' else False
        evento.eve_estado = estado
        evento.save()

        # Actualizar categoría del evento
        evento_categoria = EventosCategorias.objects.filter(eve_cat_evento_fk=evento_id).first()
        if evento_categoria:
            evento_categoria.eve_cat_categoria_fk_id = categoria
            evento_categoria.save()

        messages.success(request, "Evento actualizado correctamente.")
        return redirect('administrador:index_administrador')

    else:
        evento_categoria = EventosCategorias.objects.filter(eve_cat_evento_fk=evento).first()
        categoria_evento = evento_categoria.eve_cat_categoria_fk if evento_categoria else None
        area_categoria = categoria_evento.cat_area_fk if categoria_evento else None

        contexto = {
            'evento': evento,
            'categoria_seleccionada': categoria_evento,
            'area_seleccionada': area_categoria,
            'areas': obtener_areas_eventos(),
            'categorias': Categorias.objects.all(),
        }

        return render(request, 'app_administrador/modificarInformacion.html', contexto)

@require_http_methods(["GET", "POST"])
@login_required(login_url='login')  # Protege la vista para usuarios logueados
def ver_proyectos(request: HttpRequest, evento_id):
    estado = request.GET.get('estado')

    # Obtener el evento
    evento = get_object_or_404(Eventos, pk=evento_id)

    # Filtrar proyectos según evento y estado
    proyectos_eventos = Proyecto.objects.filter(
        pro_evento_fk=evento,
        pro_estado=estado
    )
    # Construir lista de diccionarios con datos para la plantilla
    proyectos = []
    for p in proyectos_eventos:
        expositores = ParticipantesEventos.objects.filter(par_eve_proyecto=p)
        nombres_expositores = [
            f"{exp.par_eve_participante_fk.usuario.first_name} {exp.par_eve_participante_fk.usuario.last_name}"
            for exp in expositores
        ]
        proyectos.append({
        'pro_id': p.id,
        'pro_codigo': p.pro_codigo,
        'pro_nombre': p.pro_nombre,
        'pro_descripcion': p.pro_descripcion,
        'documentos': p.pro_documentos,
        'estado': p.pro_estado,
        'hora_inscripcion': p.pro_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if p.pro_fecha_hora else None,
        'calificacion_final': p.pro_calificación_final,
        'expositores': nombres_expositores,  # 👈 aquí guardamos la lista de nombres
    })
    return render(request, 'app_administrador/ver_participantes.html', {
        'proyectos': proyectos,
        'evento': evento,
        'evento_nombre': evento.eve_nombre,
        'estado': estado,
        'evento_fecha_fin': evento.eve_fecha_fin.isoformat(),
        'fecha_actual': now().isoformat(),
    })


@csrf_exempt
@login_required(login_url='login')
def actualizar_estado_proyecto(request, proyecto_id, nuevo_estado):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    evento_id = request.POST.get('evento_id')
    razon_rechazo = request.POST.get('razon', '').strip()

    if not evento_id:
        return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

    try:
        proyecto = Proyecto.objects.get(id=proyecto_id, pro_evento_fk=evento_id)
    except Proyecto.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Proyecto no encontrado en el evento'}, status=404)

    evento = proyecto.pro_evento_fk

    # Actualizar estado del proyecto
    proyecto.pro_estado = nuevo_estado
    proyecto.save()

    # Buscar todos los expositores del proyecto
    expositores = ParticipantesEventos.objects.filter(par_eve_proyecto=proyecto)

    # ADMISIONES
    if nuevo_estado == 'Admitido':
        for expositor in expositores:
            participante = expositor.par_eve_participante_fk

            # Generar QR y clave por expositor
            qr_expositor = generar_pdf(participante.id, "expositor", evento_id, tipo="expositor")
            clave_acceso = generar_clave_acceso()

            expositor.par_eve_estado = "Admitido"
            expositor.par_eve_qr = qr_expositor
            expositor.par_eve_clave = clave_acceso
            expositor.save()

            # Enviar correo individual
            asunto = f"Confirmación de inscripción como expositor al evento: {evento.eve_nombre}"
            mensaje_html = render_to_string("app_administrador/correos/comprobante_inscripcion.html", {
                "nombre": participante.usuario.first_name,
                "evento": evento.eve_nombre,
                "clave": clave_acceso,
            })

            email = EmailMultiAlternatives(
                asunto,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [participante.usuario.email]
            )
            email.attach_alternative(mensaje_html, "text/html")

            # Adjuntar PDF QR
            ruta_pdf = os.path.join(settings.MEDIA_ROOT, str(qr_expositor))
            if os.path.exists(ruta_pdf):
                with open(ruta_pdf, 'rb') as f:
                    email.attach(os.path.basename(ruta_pdf), f.read(), 'application/pdf')

            email.send(fail_silently=True)

    # RECHAZOS
    elif nuevo_estado == 'Rechazado':
        if not razon_rechazo:
            razon_rechazo = "No se especificó el motivo del rechazo."

        for expositor in expositores:
            participante = expositor.par_eve_participante_fk

            expositor.par_eve_estado = "Rechazado"
            expositor.par_eve_clave = ""
            expositor.par_eve_qr = ""
            expositor.save()

            # Enviar correo individual
            asunto = f"Notificación de rechazo - {evento.eve_nombre}"
            mensaje_html = render_to_string("app_administrador/correos/rechazo_participantes.html", {
                "nombre": participante.usuario.first_name,
                "evento": evento.eve_nombre,
                "razon": razon_rechazo
            })

            email = EmailMultiAlternatives(
                asunto,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [participante.usuario.email]
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send(fail_silently=True)

    # Redirigir correctamente
    url = reverse('administrador:ver_participantes', kwargs={'evento_id': evento_id})
    return redirect(f'{url}?estado={nuevo_estado}')


@login_required(login_url='login')  # Protege la vista para usuarios logueados
def ver_asistentes(request: HttpRequest, evento_id):
    estado = request.GET.get('estado')

    # Obtener los asistentes del evento utilizando el ORM de Django
    asistentes_evento = AsistentesEventos.objects.select_related('asi_eve_asistente_fk').filter(
        asi_eve_evento_fk=evento_id,
        asi_eve_estado=estado)
    
    evento = get_object_or_404(Eventos, id=evento_id)

    #obtener asistentes admitidos
    asistentes_admitidos = AsistentesEventos.objects.filter(
        asi_eve_evento_fk=evento_id,
        asi_eve_estado='Admitido'
    ).count()
    
    # Preparar los datos
    asistentes_data = []
    for ae in asistentes_evento:
        a = ae.asi_eve_asistente_fk
        asistentes_data.append({
            'asi_id': a.id,
            'asi_nombre': a.usuario.first_name + ' ' + a.usuario.last_name,
            'asi_correo': a.usuario.email,
            'asi_telefono': a.usuario.telefono,
            'documentos': ae.asi_eve_soporte.url if ae.asi_eve_soporte else None,
            'estado': ae.asi_eve_estado,
            'hora_inscripcion': ae.asi_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if ae.asi_eve_fecha_hora else None,
        })

    return render(request, 'app_administrador/ver_asistentes.html', {
        'asistentes': asistentes_data,
        'evento': evento,
        'evento_nombre': evento.eve_nombre,
        'estado': estado,
        'evento_fecha_fin': evento.eve_fecha_fin.isoformat(),
        'fecha_actual': now().isoformat(),
        'asistentes_admitidos': asistentes_admitidos,
    })
    
@csrf_exempt
@login_required(login_url='login')  # Protege la vista para usuarios logueados
def actualizar_estado_asistente(request, asistente_id, nuevo_estado):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    evento_id = request.POST.get('evento_id')
    motivo = request.POST.get('motivo', '').strip()

    if not evento_id:
        return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

    # Buscar el asistente_evento
    asistente_evento = AsistentesEventos.objects.filter(
        asi_eve_asistente_fk=asistente_id,
        asi_eve_evento_fk=evento_id
    ).first()

    if not asistente_evento:
        return JsonResponse({'status': 'error', 'message': 'Asistente no encontrado en el evento'}, status=404)

    evento = asistente_evento.asi_eve_evento_fk

    # ✅ Verificar límite de aforo antes de admitir
    if nuevo_estado == 'Admitido':
        qr_participante = generar_pdf(asistente_id, "Asistente", evento_id, tipo="asistente")
        clave_acceso = generar_clave_acceso()
    else:
        qr_participante = None
        clave_acceso = 0

    # ✅ Actualizar los valores
    asistente_evento.asi_eve_estado = nuevo_estado
    asistente_evento.asi_eve_qr = qr_participante
    asistente_evento.asi_eve_clave = clave_acceso
    asistente_evento.save()

    asistente = get_object_or_404(Asistentes, id=asistente_id)

    # ✅ Envío de correo si es admitido
    if nuevo_estado == 'Admitido':
        asunto = f"Confirmación de inscripción como asistente al evento: {evento.eve_nombre}"
        mensaje_html = render_to_string("app_administrador/correos/notificacion_admitido_asistente.html", {
            "nombre": asistente.usuario.first_name,
            "evento": evento.eve_nombre,
            "clave": clave_acceso,
        })

        email = EmailMultiAlternatives(
            asunto,
            "",  # cuerpo de texto plano (opcional)
            settings.DEFAULT_FROM_EMAIL,
            [asistente.usuario.email]
        )
        email.attach_alternative(mensaje_html, "text/html")

        ruta_pdf = os.path.join(settings.MEDIA_ROOT, str(qr_participante))
        if os.path.exists(ruta_pdf):
            with open(ruta_pdf, 'rb') as f:
                email.attach(os.path.basename(ruta_pdf), f.read(), 'application/pdf')

        email.send(fail_silently=True)

    elif nuevo_estado == 'Rechazado':
        asunto = f"Inscripción rechazada al evento: {evento.eve_nombre}"
        mensaje_html = render_to_string("app_administrador/correos/correo_rechazo_asistente.html", {
            "nombre": asistente.usuario.first_name,
            "evento": evento.eve_nombre,
            "motivo": motivo or "No se especificó motivo.",
            "anio": timezone.now().year,
        })

        email = EmailMultiAlternatives(
            asunto,
            "",
            settings.DEFAULT_FROM_EMAIL,
            [asistente.usuario.email]
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send(fail_silently=True)

    # ✅ Redirigir correctamente
    url = reverse('administrador:ver_asistentes', kwargs={'evento_id': evento_id})
    return redirect(f'{url}?estado={nuevo_estado}')


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

    # Subconsulta: promedio por criterio y proyecto
    subquery = (
        Calificaciones.objects
        .values('clas_proyecto_fk', 'cal_criterio_fk')
        .annotate(promedio_criterio=Avg('cal_valor'))
    )

    # Diccionario para acumular los promedios ponderados por proyecto
    ranking_dict = {}

    for row in subquery:
        criterio = Criterios.objects.filter(id=row['cal_criterio_fk'], cri_evento_fk=evento_id).first()
        if criterio:
            proyecto_id = row['clas_proyecto_fk']
            ponderado = row['promedio_criterio'] * criterio.cri_peso / 100

            if proyecto_id not in ranking_dict:
                ranking_dict[proyecto_id] = 0
            ranking_dict[proyecto_id] += ponderado

    # Ordenar por puntaje final descendente
    ranking_ordenado = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    # Construir lista final para el template
    ranking = []
    for proyecto_id, puntaje in ranking_ordenado:
        proyecto = Proyecto.objects.get(id=proyecto_id)

        # Obtener expositores vinculados al proyecto en este evento
        expositores = ParticipantesEventos.objects.filter(
            par_eve_proyecto=proyecto,
            par_eve_evento_fk=evento
        )

        lista_expositores = [
            f"{e.par_eve_participante_fk.usuario.first_name} {e.par_eve_participante_fk.usuario.last_name}"
            for e in expositores
        ]

        ranking.append({
            'id': proyecto.id,
            'proyecto': proyecto.pro_nombre,
            'expositores': lista_expositores,
            'puntaje_final': round(puntaje, 2)
        })

    return render(request, 'app_administrador/posiciones.html', {
        'ranking': ranking,
        'evento': evento,
        'administrador': request.session.get('admin_nombre'),
    })

def descargar_ranking_pdf(request, evento_id):
    evento = Eventos.objects.get(id=evento_id)
    ranking = obtener_ranking(evento_id)  

    html_string = render_to_string('app_administrador/ranking_pdf.html', {
        'evento': evento,
        'ranking': ranking,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ranking_evento_{evento_id}.pdf"'

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response



def detalles_calificaciones(request, evento_id, proyecto_id):
    """
    Muestra las calificaciones detalladas de un proyecto en un evento,
    agrupadas por evaluador y con cálculo de puntajes ponderados.
    """

    # Obtener proyecto y evento
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    evento = get_object_or_404(Eventos, id=evento_id)

    # Traer todas las calificaciones del proyecto en ese evento
    calificaciones = (
        Calificaciones.objects.filter(
            clas_proyecto_fk=proyecto,
            cal_criterio_fk__cri_evento_fk=evento
        )
        .select_related('cal_evaluador_fk', 'cal_criterio_fk')
    )

    # Estructura para agrupar por evaluador
    evaluadores_data = {}

    for cal in calificaciones:
        evaluador = cal.cal_evaluador_fk
        criterio = cal.cal_criterio_fk

        # Inicializar datos de evaluador si no existe en el diccionario
        if evaluador.id not in evaluadores_data:
            evaluadores_data[evaluador.id] = {
                'evaluador': evaluador,
                'calificaciones': [],
                'puntaje_total': 0.0,
            }

        # Calcular puntaje ponderado para este criterio
        ponderado = float(cal.cal_valor) * float(criterio.cri_peso) / 100

        # Agregar detalle de calificación
        evaluadores_data[evaluador.id]['calificaciones'].append({
            'criterio': criterio.cri_descripcion,
            'peso': criterio.cri_peso,
            'valor': cal.cal_valor,
            'ponderado': round(ponderado, 2),
        })

        # Sumar al total ponderado del evaluador
        evaluadores_data[evaluador.id]['puntaje_total'] += ponderado

    # Redondear totales de cada evaluador
    for data in evaluadores_data.values():
        data['puntaje_total'] = round(data['puntaje_total'], 2)

    # Renderizar plantilla
    return render(request, 'app_administrador/detalle_calificaciones.html', {
        'proyecto': proyecto,
        'evento': evento,
        'evaluadores_data': evaluadores_data.values(),
        'administrador': request.session.get('admin_nombre'),
    })


# Vista: Detalle de calificación de un proyecto por un evaluador
@login_required(login_url='login')
def detalle_calificacion(request, proyecto_id, evaluador_id, evento_id):
    """
    Muestra el detalle de calificaciones de un evaluador hacia un proyecto específico
    en un evento, incluyendo criterios, puntajes ponderados y comentarios.
    """

    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
    evento = get_object_or_404(Eventos, id=evento_id)

    # Obtener todas las calificaciones de ese evaluador a ese proyecto
    calificaciones = (
        Calificaciones.objects.filter(
            clas_proyecto_fk=proyecto,
            cal_evaluador_fk=evaluador,
            cal_criterio_fk__cri_evento_fk=evento
        )
        .select_related('cal_criterio_fk')
    )

    calificaciones_info = []
    puntaje_total = 0.0

    for cal in calificaciones:
        criterio = cal.cal_criterio_fk
        ponderado = float(cal.cal_valor) * float(criterio.cri_peso) / 100
        puntaje_total += ponderado

        calificaciones_info.append({
            'criterio': criterio.cri_descripcion,
            'peso': float(criterio.cri_peso),
            'valor': float(cal.cal_valor),
            'ponderado': round(ponderado, 2),
            'comentario': cal.cal_comentario if hasattr(cal, 'cal_comentario') else ""
        })

    return render(request, 'app_administrador/detalle_calificacion_participante.html', {
        'proyecto': proyecto,
        'evaluador': evaluador,
        'evento': evento,
        'calificaciones_info': calificaciones_info,
        'puntaje_total': round(puntaje_total, 2),
        'administrador': request.session.get('admin_nombre'),
    })

@login_required(login_url='login')
def ver_evaluadores(request: HttpRequest, evento_id):
    estado = request.GET.get('estado')

    # Obtener los evaluadores del evento
    evaluadores_evento = EvaluadoresEventos.objects.select_related('eva_eve_evaluador_fk').filter(
        eva_eve_evento_fk=evento_id,
        eva_estado=estado
    )
    
    evento = get_object_or_404(Eventos, id=evento_id)

    # Preparar los datos con nombres consistentes
    evaluadores_data = []
    for ee in evaluadores_evento:
        e = ee.eva_eve_evaluador_fk
        evaluadores_data.append({
            'eva_id': e.id,  # Cambiado de asi_id a eva_id
            'eva_nombre': e.usuario.first_name + ' ' + e.usuario.last_name,  # Cambiado de asi_nombre a eva_nombre
            'eva_correo': e.usuario.email,  # Cambiado de asi_correo a eva_correo
            'eva_telefono': e.usuario.telefono if e.usuario.telefono else 'No registrado',  # Cambiado de asi_telefono a eva_telefono
            'estado': ee.eva_estado,
            'documento': ee.eva_eve_documentos,
            'area_evaluar': ee.eva_eve_areas_interes,
            'hora_inscripcion': ee.eva_eve_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if ee.eva_eve_fecha_hora else 'No registrada',
        })

    return render(request, 'app_administrador/ver_evaluadores.html', {
        'evaluadores': evaluadores_data,
        'evento': evento,
        'evento_id': evento_id,  # Agregado para usar en el template
        'evento_nombre': evento.eve_nombre,
        'estado': estado,
        'evento_fecha_fin': evento.eve_fecha_fin.isoformat(),
        'fecha_actual': now().isoformat(),
    })

@csrf_exempt
@login_required(login_url='login')
def actualizar_estado_evaluador(request, evaluador_id, nuevo_estado):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')

        if not evento_id:
            return JsonResponse({'status': 'error', 'message': 'ID de evento no proporcionado'}, status=400)

        # Generar PDF y clave de acceso si es admitido
        if nuevo_estado == 'Admitido':
            qr_evaluador = generar_pdf(evaluador_id, "Evaluador", evento_id, tipo="evaluador")
            clave_acceso = generar_clave_acceso()
        else:
            qr_evaluador = None
            clave_acceso = 0

        # Buscar relación Evaluador-Evento
        try:
            evaluador_evento = EvaluadoresEventos.objects.get(
                eva_eve_evaluador_fk=evaluador_id,
                eva_eve_evento_fk=evento_id
            )
        except EvaluadoresEventos.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Evaluador no encontrado en el evento'}, status=404)

        # Actualizar datos
        evaluador_evento.eva_estado = nuevo_estado
        evaluador_evento.eva_eve_qr = qr_evaluador
        evaluador_evento.eva_clave_acceso = clave_acceso
        evaluador_evento.save()

        # Si fue admitido, enviar correo con clave y QR
        if nuevo_estado == 'Admitido':
            evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
            evento = evaluador_evento.eva_eve_evento_fk

            asunto = f"Confirmación de participación como evaluador en el evento: {evento.eve_nombre}"

            mensaje_html = render_to_string("app_administrador/correos/admision_evaluador.html", {
                "nombre": evaluador.usuario.first_name,
                "evento": evento.eve_nombre,
                "clave": clave_acceso,
                "anio": timezone.now().year,
            })

            email = EmailMultiAlternatives(
                asunto,
                "",  # opcional: cuerpo de texto plano
                settings.DEFAULT_FROM_EMAIL,
                [evaluador.usuario.email]
            )
            email.attach_alternative(mensaje_html, "text/html")

            ruta_pdf = os.path.join(settings.MEDIA_ROOT, str(qr_evaluador))

            if os.path.exists(ruta_pdf):
                with open(ruta_pdf, 'rb') as f:
                    email.attach(os.path.basename(ruta_pdf), f.read(), 'application/pdf')

            email.send(fail_silently=True)
            
        elif nuevo_estado == 'Rechazado':
            evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
            evento = evaluador_evento.eva_eve_evento_fk

            asunto = f"Inscripción rechazada como evaluador para el evento: {evento.eve_nombre}"

            mensaje_html = render_to_string("app_administrador/correos/rechazo_evaluador.html", {
                "nombre": evaluador.usuario.first_name,
                "evento": evento.eve_nombre,
                "clave": clave_acceso,
                "motivo": request.POST.get('motivo', 'No especificado'),
                "anio": timezone.now().year,
            })

            email = EmailMultiAlternatives(
                asunto,
                "",  # opcional: cuerpo de texto plano
                settings.DEFAULT_FROM_EMAIL,
                [evaluador.usuario.email]
            )
            email.attach_alternative(mensaje_html, "text/html")

            ruta_pdf = os.path.join(settings.MEDIA_ROOT, str(qr_evaluador))

            if os.path.exists(ruta_pdf):
                with open(ruta_pdf, 'rb') as f:
                    email.attach(os.path.basename(ruta_pdf), f.read(), 'application/pdf')

            email.send(fail_silently=True)
        # Redirigir con estado
        url = reverse('administrador:ver_evaluadores', kwargs={'evento_id': evento_id})
        return redirect(f'{url}?estado={nuevo_estado}')

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required(login_url='login')  # Protege la vista para usuarios logueados
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
                    return redirect('administrador:index_administrador')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('administrador:index_administrador')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('administrador:index_administrador')

    return redirect('administrador:index_administrador')

def obtener_emails_por_destinatarios(destinatarios, ids_por_tipo=None):
    correos = []

    if ids_por_tipo is None:
        ids_por_tipo = {}

    if 'todos' in destinatarios:
        correo_asistentes = Asistentes.objects.values_list('usuario__email', flat=True)
        correo_participantes = Participantes.objects.values_list('usuario__email', flat=True)
        correo_evaluadores = Evaluadores.objects.values_list('usuario__email', flat=True)
        correos = list(correo_asistentes) + list(correo_participantes) + list(correo_evaluadores)
    else:
        if 'asistentes' in destinatarios:
            ids = ids_por_tipo.get('asistentes', [])
            correo_asistentes = Asistentes.objects.filter(id__in=ids).values_list('usuario__email', flat=True)
            correos += list(correo_asistentes)
        if 'participantes' in destinatarios:
            ids = ids_por_tipo.get('participantes', [])
            correo_participantes = Participantes.objects.filter(id__in=ids).values_list('usuario__email', flat=True)
            correos += list(correo_participantes)
        if 'evaluadores' in destinatarios:
            ids = ids_por_tipo.get('evaluadores', [])
            correo_evaluadores = Evaluadores.objects.filter(id__in=ids).values_list('usuario__email', flat=True)
            correos += list(correo_evaluadores)

    return list(set(correos))

@login_required(login_url='login')  # Protege la vista para usuarios logueados
def enviar_correo(request, evento_id):
    # 🔹 1. Obtener el evento
    try:
        evento = Eventos.objects.get(id=evento_id)
    except Eventos.DoesNotExist:
        return render(request, 'app_administrador/correos/enviar_correo.html', {
            'error_envio': 'El evento no existe.',
        })

    # 🔹 2. Obtener asistentes admitidos
    asistentes = Asistentes.objects.filter(
        id__in=AsistentesEventos.objects.filter(
            asi_eve_evento_fk_id=evento_id,
            asi_eve_estado__iexact='Admitido'
        ).values_list('asi_eve_asistente_fk_id', flat=True)
    )

    # 🔹 3. Obtener evaluadores admitidos
    evaluadores = Evaluadores.objects.filter(
        id__in=EvaluadoresEventos.objects.filter(
            eva_eve_evento_fk_id=evento_id,
            eva_estado__iexact='Admitido'
        ).values_list('eva_eve_evaluador_fk_id', flat=True)
    )

    # 🔹 4. Obtener participantes admitidos
    participantes = Participantes.objects.filter(
        id__in=ParticipantesEventos.objects.filter(
            par_eve_evento_fk_id=evento_id,
            par_eve_estado__iexact='Admitido'
        ).values_list('par_eve_participante_fk_id', flat=True)
    )

    # 🔹 5. Armar lista de roles para el template
    roles = [
        {'key': 'asistentes', 'nombre': 'Asistentes', 'usuarios': asistentes},
        {'key': 'participantes', 'nombre': 'Participantes', 'usuarios': participantes},
        {'key': 'evaluadores', 'nombre': 'Evaluadores', 'usuarios': evaluadores},
    ]

    # 🔹 6. Procesar formulario POST
    if request.method == 'POST':
        try:
            asunto = request.POST.get('asunto', '').strip()
            contenido = request.POST.get('contenido', '').strip()
            archivos = request.FILES.getlist('archivos')
            destinatarios = request.POST.getlist('destinatarios')

            # 🔸 Validaciones
            if not destinatarios:
                return render(request, 'app_administrador/correos/enviar_correo.html', {
                    'roles': roles,
                    'evento': evento,
                    'error_envio': 'Debes seleccionar al menos un destinatario.',
                })

            if not contenido:
                return render(request, 'app_administrador/correos/enviar_correo.html', {
                    'roles': roles,
                    'evento': evento,
                    'error_envio': 'El mensaje del correo no puede estar vacío.',
                })

            # 🔹 7. Capturar IDs seleccionados
            ids_por_tipo = {
                'asistentes': request.POST.getlist('asistentes_seleccionados'),
                'participantes': request.POST.getlist('participantes_seleccionados'),
                'evaluadores': request.POST.getlist('evaluadores_seleccionados'),
            }

            # 🔹 8. Obtener correos
            correos = obtener_emails_por_destinatarios(destinatarios, ids_por_tipo)

            if not correos:
                return render(request, 'app_administrador/correos/enviar_correo.html', {
                    'roles': roles,
                    'evento': evento,
                    'error_envio': 'No se encontraron correos para los destinatarios seleccionados.',
                })

            # 🔹 9. Enviar correo
            email = EmailMessage(asunto, contenido, to=correos)
            email.content_subtype = 'html'
            for archivo in archivos:
                email.attach(archivo.name, archivo.read(), archivo.content_type)
            email.send()

            return render(request, 'app_administrador/correos/enviar_correo.html', {
                'roles': roles,
                'evento': evento,
                'envio_exitoso': True,
            })

        except Exception as e:
            print("Error al enviar correo:", e)
            return render(request, 'app_administrador/correos/enviar_correo.html', {
                'roles': roles,
                'evento': evento,
                'error_envio': str(e),
            })

    # 🔹 10. GET → mostrar formulario
    return render(request, 'app_administrador/correos/enviar_correo.html', {
        'roles': roles,
        'evento': evento,
    })

@login_required(login_url='login')
def guardar_memorias(request):
    if request.method == 'POST':
        url = request.POST.get('url_memorias')
        evento_id = request.POST.get('evento_id')
        
        try:
            evento = Eventos.objects.get(id=evento_id)
            evento.eve_memorias = url
            evento.save()
            return redirect(f"{reverse('administrador:index_administrador')}?exito_memorias=1")
        except Eventos.DoesNotExist:
            messages.error(request, "No se encontró el evento.")

    return redirect('administrador:index_administrador')



#Rutas relativas de los diseños por defecto
DEFAULT_VERTICAL = 'defaults/certificado_vertical.png'
DEFAULT_HORIZONTAL = 'defaults/certificado_defecto.png'

def is_default_design(path):
    return DEFAULT_VERTICAL in path or DEFAULT_HORIZONTAL in path
  # si lo estás usando en diseño

@login_required(login_url='login')
def configuracion_certificados(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    try:
        certificado = Certificado.objects.get(evento_fk=evento)
        diseño = True if certificado.diseño else False
        firma = True if certificado.firma else False
    except Certificado.DoesNotExist:
        certificado = None
        diseño = False
        firma = False

    if request.method == 'POST':
        if not certificado:
            certificado = Certificado(evento_fk=evento)  # ⚠️ SE CREA AQUÍ

        certificado.certifica = request.POST.get('nombre_certificador')
        certificado.tipografia = request.POST.get('tipografia')
        certificado.orientacion = request.POST.get('orientacion')
        certificado.lugar_expedicion = request.POST.get('lugar_expedicion')

        # --------------------------
        # Procesamiento del diseño
        # --------------------------
        con_diseno = request.POST.get('con_diseno')
        if con_diseno == 'si' and 'diseno' in request.FILES:
            if certificado.diseño and os.path.isfile(certificado.diseño.path) and not is_default_design(certificado.diseño.path):
                os.remove(certificado.diseño.path)
            certificado.diseño = request.FILES['diseno']
        elif con_diseno == 'no':
            if certificado.diseño and os.path.isfile(certificado.diseño.path) and not is_default_design(certificado.diseño.path):
                os.remove(certificado.diseño.path)
            certificado.diseño = None

        # --------------------------
        # Procesamiento de la firma
        # --------------------------
        con_firma = request.POST.get('con_firma')
        if con_firma == 'si':
            certificado.firma_nombre = request.POST.get('firma_nombre')
            certificado.firma_cargo = request.POST.get('firma_cargo')
            if 'firma' in request.FILES:
                if certificado.firma and os.path.isfile(certificado.firma.path):
                    os.remove(certificado.firma.path)
                certificado.firma = request.FILES['firma']
        else:
            if certificado.firma and os.path.isfile(certificado.firma.path):
                os.remove(certificado.firma.path)
            certificado.firma = None
            certificado.firma_nombre = ''
            certificado.firma_cargo = ''

        certificado.save()

        # --------------------------
        # Asignar diseño por defecto si no hay diseño cargado
        # --------------------------
        if not certificado.diseño:
            if certificado.orientacion == 'vertical':
                certificado.diseño = DEFAULT_VERTICAL
            elif certificado.orientacion == 'horizontal':
                certificado.diseño = DEFAULT_HORIZONTAL
            certificado.save()

        return redirect(f"{reverse('administrador:configuracion_certificados', args=[evento.id])}?guardado=1")

    guardado = request.GET.get('guardado') == '1'

    return render(request, 'app_administrador/configuracion_certificados.html', {
        'evento': evento,
        'guardado': guardado,
        'certificado': certificado,
        'con_diseno': diseño,
        'con_firma': firma,
        'orientacion': certificado.orientacion if certificado else 'vertical',
        
    })

    
@login_required(login_url='login')
def descargar_certificado_pdf(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    certificado = get_object_or_404(Certificado, evento_fk=evento)

    try:
        locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    fecha_formateada = datetime.now().strftime('%d de %B de %Y')
    
    # Renderizar plantilla HTML con los datos del certificado
    html_string = render_to_string('app_administrador/pdf_certificado.html', {
        'certificado': certificado,
        'evento': evento,
        'now': fecha_formateada,
    })

    # Generar PDF desde HTML
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()

    # Retornar respuesta como PDF descargable
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="certificado_{evento.id}.pdf"'

    return response

@login_required(login_url='login')
def enviar_certificado_participantes(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    # Obtener participantes admitidos
    participantes = Participantes.objects.filter(
        id__in=ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento_id,
            par_eve_estado__iexact='Admitido'
        ).values_list('par_eve_participante_fk_id', flat=True)
    )
    
    if request.method == 'POST':
        print("Enviando certificados a participantes...")
        correos_enviados = []
        errores = []

        for participante in participantes:
            print(f"Procesando participante: {participante.usuario.email}")
            contexto = {
                'evento': evento,
                'participante': participante
            }

            mensaje = render_to_string('app_administrador/correos/correo_certificado.html', contexto)
            email = EmailMessage(
                subject=f"Certificado de participación en el evento {evento.eve_nombre}",
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[participante.usuario.email]
            )
            email.content_subtype = 'html'

            # Generar y adjuntar PDF
            try:
                pdf_content = generar_certificados_expositores(request, evento_id, "expositor", participante.id)
                if isinstance(pdf_content, HttpResponse):
                    continue  # Saltar si hubo error en la generación
                email.attach(
                    f'certificado_{getattr(participante.usuario, "documento_identidad", participante.id)}.pdf',
                    pdf_content,
                    'application/pdf'
                )
                email.send(fail_silently=False)
                correos_enviados.append(participante.usuario.email)
            except Exception as e:
                errores.append(str(e))
                print(f"Error enviando correo a {participante.usuario.email}: {e}")

        print(f"Certificados enviados a: {correos_enviados}")
        return redirect('administrador:index_administrador')

    return HttpResponse("Método no permitido", status=405)

@login_required(login_url='login')
def enviar_certificado_asistentes(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    
    participantes = Asistentes.objects.filter(
        id__in=AsistentesEventos.objects.filter(
            asi_eve_evento_fk=evento_id,
            asi_eve_estado__iexact='Admitido'
        ).values_list('asi_eve_asistente_fk_id', flat=True)
    )

    if request.method == 'POST':
        correos_enviados = []
        for participante in participantes:
            contexto = {
                'evento': evento,
                'participante': participante
            }

            mensaje = render_to_string('app_administrador/correos/correo_certificado.html', contexto)

            email = EmailMessage(
                subject=f"Certificado de participación en el evento {evento.eve_nombre}",
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[participante.usuario.email]
            )
            email.content_subtype = 'html'

            pdf_content = generar_certificados(request, evento_id, "asistente", participante.id)
            email.attach(
                f'certificado_{participante.usuario.documento_identidad}.pdf',
                pdf_content,
                'application/pdf'
            )

            email.send(fail_silently=False)
            correos_enviados.append(participante.usuario.email)

        return redirect('administrador:index_administrador')
    
    # 🔹 Esta línea es la que faltaba:
    return HttpResponse("Vista de envío de certificados lista para ejecutar (GET).")

@login_required(login_url='login') 
def enviar_certificado_evaluadores(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    

    # Obtener Evaluadores admitidos
    participantes =Evaluadores.objects.filter(
        id__in=EvaluadoresEventos.objects.filter(
            eva_eve_evento_fk=evento_id,
            eva_estado__iexact='Admitido'
        ).values_list('eva_eve_evaluador_fk_id', flat=True)
    )

    
    if request.method == 'POST':

        correos_enviados = []
        for participante in participantes:
            contexto = {
                'evento': evento,
                'participante': participante
            }

            mensaje = render_to_string('app_administrador/correos/correo_certificado.html', contexto)

            email = EmailMessage(
                subject=f"Certificado de participación en el evento { evento.eve_nombre}",
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[participante.usuario.email]
            )
            email.content_subtype = 'html'

            # Adjuntar certificado PDF
            pdf_content = generar_certificados(request,evento_id, "evaluador", participante.id )
            email.attach(f'certificado_{participante.usuario.documento_identidad}.pdf', pdf_content, 'application/pdf')

            email.send(fail_silently=False)
            correos_enviados.append(participante.usuario.email)

        return redirect('administrador:index_administrador')

@csrf_exempt 
@login_required(login_url='login')
def enviar_certificado_reconocimiento(request, evento_id, proyecto_id):
    if request.method == 'POST':
        evento = get_object_or_404(Eventos, id=evento_id)
        participante_eventos = ParticipantesEventos.objects.filter(par_eve_proyecto=proyecto_id, par_eve_evento_fk=evento_id)
        
        for participante in participante_eventos:
            participante = participante.par_eve_participante_fk
            participante_id = participante.id

            contexto = {
                'evento': evento,
                'participante': participante
            }

            mensaje = render_to_string('app_administrador/correos/certificado_reconocimiento.html', contexto)

            email = EmailMessage(
                subject=f"Reconocimiento en el evento {evento.eve_nombre}",
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[participante.usuario.email]
            )
            email.content_subtype = 'html'

            # Adjuntar certificado PDF
            pdf_content = generar_reconocmiento(request, evento_id, participante_id)
            email.attach(f'Reconocmiento_{participante.usuario.documento_identidad}.pdf', pdf_content, 'application/pdf')

            email.send(fail_silently=False)

        return JsonResponse({'success': True, 'message': 'Reconocimiento enviado correctamente.'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)



def modificar_certificados(request,evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    certificado = get_object_or_404(Certificado, evento_fk=evento_id)

    # Formatear fecha actual en español
    meses_es = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    fecha_actual = now()
    mes_es = meses_es[fecha_actual.strftime('%B')]
    fecha_formateada = fecha_actual.strftime(f'%d de {mes_es} de %Y')

    context = {
        'evento': evento,
        'certificado': certificado,
        'fecha_actual': fecha_formateada,
        'orientacion': certificado.orientacion,
    }

    return render(request, 'app_administrador/modificar_certificado.html', context)

@login_required(login_url='login')
def listar_evaluadores_ajax(request, evento_id, proyecto_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    evaluadores = EvaluadoresEventos.objects.filter(
        eva_eve_evento_fk=evento,
        eva_estado='Admitido'
    ).select_related('eva_eve_evaluador_fk')

    data = []
    for ev in evaluadores:
        # Ahora usamos el evaluador real
        asignado = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=proyecto,
            eva_pro_evaluador_fk=ev.eva_eve_evaluador_fk  # 👈 cambio clave
        ).exists()

        data.append({
            "id": ev.eva_eve_evaluador_fk.id,  # id del evaluador
            "nombre": f"{ev.eva_eve_evaluador_fk.usuario.first_name} {ev.eva_eve_evaluador_fk.usuario.last_name}",
            "area": ev.eva_eve_areas_interes,
            "asignado": asignado
        })

    return JsonResponse({"evaluadores": data})

@login_required(login_url='login')
def asignar_evaluador_ajax(request, evento_id, proyecto_id, evaluador_id):
    if request.method == 'POST':

        if not evaluador_id:
            return JsonResponse({"success": False, "message": "No se recibió el evaluador."}, status=400)

        evento = get_object_or_404(Eventos, id=evento_id)
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        evaluador = get_object_or_404(Evaluadores, id=evaluador_id)

        # Verificar si ya está asignado
        if EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=proyecto,
            eva_pro_evaluador_fk=evaluador
        ).exists():
            return JsonResponse({"success": False, "message": "Este evaluador ya está asignado al proyecto."})

        # Crear asignación
        EvaluadorProyecto.objects.create(
            eva_pro_proyecto_fk=proyecto,
            eva_pro_evaluador_fk=evaluador
        )

        # Enviar correo usando plantilla HTML
        if evaluador.usuario.email:
            subject = "Asignación de proyecto"
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [evaluador.usuario.email]

            context = {
                "evaluador": evaluador.usuario.first_name,
                "evento": evento,
                "proyecto": proyecto,
                "sitio": "EventSoft"
            }

            html_content = render_to_string("app_administrador/correos/asignacion_evaluador.html", context)

            msg = EmailMultiAlternatives(subject, "", from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        return JsonResponse({"success": True, "message": "Evaluador asignado y notificado por correo."})

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@login_required(login_url='login')
def designar_evaluador_ajax(request, evento_id, proyecto_id, evaluador_id):
    if request.method == 'POST':

        if not evaluador_id:
            return JsonResponse({"success": False, "message": "No se recibió el evaluador."}, status=400)

        # Obtener evento y proyecto
        evento = get_object_or_404(Eventos, id=evento_id)
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)

        # Obtener el evaluador (ojo: desde Evaluadores, no EvaluadoresEventos)
        evaluador = get_object_or_404(Evaluadores, id=evaluador_id)
        
        #Eliminar Asignación
        EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=proyecto,
            eva_pro_evaluador_fk=evaluador
        ).delete()

        return JsonResponse({"success": True, "message": "Asignaciónn cancelada correctamente."})

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@login_required
def config_inscripcion(request, evento_id):
    if request.method == "POST":
        data = json.loads(request.body)
        estado = data.get("estado")# 1 = activo, 0 = inactivo
        tipo = data.get("tipo")  # "evaluador" o "expositor"

        # Aquí guardas en tu modelo según el tipo (evaluador o expositor)
        if tipo == "Evaluador":
            evento = get_object_or_404(Eventos, id=evento_id)
            evento.eve_habilitar_evaluadores = estado
            evento.save()
        elif tipo == "Expositor":
            evento = get_object_or_404(Eventos, id=evento_id)
            evento.eve_habilitar_participantes = estado
            evento.save()


        return JsonResponse({"success": True, "message": f"{tipo} actualizado a {estado}"})
    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)



from django.http import FileResponse


@login_required
def descargar_documento(request, participante_id):
    """
    Permite descargar el documento del participante autenticado.
    Solo accesible si el usuario está logueado.
    """
    try:
        participante_evento = ParticipantesEventos.objects.get(id=participante_id)
        documento = participante_evento.par_eve_documentos
        if not documento:
            raise Http404("Documento no encontrado")

        # Devuelve el archivo de forma segura
        return FileResponse(documento.open('rb'), as_attachment=True, filename=documento.name)

    except ParticipantesEventos.DoesNotExist:
        raise Http404("Participante no encontrado")

from django.http import FileResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET

@require_GET
def listar_evaluadores_pendientes(request):
    # Obtener evaluadores con estado "Pendiente de Revisión"
    evaluadores_pendientes = EvaluadoresEventos.objects.filter(
        eva_estado="Pendiente de Revisión"
    ).select_related('eva_eve_evaluador_fk')

    # Obtener parámetros de orden si los hay (?orden=nombre o ?orden=experticia)
    orden = request.GET.get('orden', None)
    if orden:
        evaluadores_pendientes = evaluadores_pendientes.order_by(orden)

    # Convertir a JSON estructurado
    data = []
    for evaluador_evento in evaluadores_pendientes:
        evaluador = evaluador_evento.eva_eve_evaluador_fk
        data.append({
            "id": evaluador.id,
            "nombre_completo": f"{evaluador.eva_nombre} {evaluador.eva_apellido}",
            "correo": evaluador.eva_correo,
            "telefono": evaluador.eva_telefono,
            "areas_interes": evaluador_evento.eva_eve_areas_interes,
            "estado": evaluador_evento.eva_estado,
            "documento_soporte": evaluador_evento.eva_eve_documentos.url if evaluador_evento.eva_eve_documentos else None,
            "fecha_postulacion": evaluador_evento.eva_eve_fecha_hora,
        })

    return JsonResponse({"evaluadores": data}, safe=False)
@login_required
def evaluadores_pendientes(request):
    evaluadores = EvaluadoresEventos.objects.filter(eva_estado='Pendiente de Revisión')
    return render(request, 'app_administrador/evaluadores_pendientes.html', {'evaluadores': evaluadores})


@login_required
def descargar_documento_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(EvaluadoresEventos, id=evaluador_id)
    if evaluador.eva_eve_documentos:
        return FileResponse(evaluador.eva_eve_documentos.open(), as_attachment=True)
    return HttpResponseForbidden("El evaluador no tiene documentos disponibles.")


@login_required
def aprobar_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(EvaluadoresEventos, id=evaluador_id)
    evaluador.eva_estado = 'Aprobado'
    evaluador.save()
    return render(request, 'app_administrador/evaluador_aprobado.html', {'evaluador': evaluador})


@login_required
def rechazar_evaluador(request, evaluador_id):
    evaluador = get_object_or_404(EvaluadoresEventos, id=evaluador_id)
    evaluador.eva_estado = 'Rechazado'
    evaluador.save()
    return render(request, 'app_administrador/evaluador_rechazado.html', {'evaluador': evaluador})

@csrf_exempt
@require_POST
def cambiar_estado_evaluador(request, evaluador_id):
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        evaluador_evento = EvaluadoresEventos.objects.get(id=evaluador_id)
        evaluador_evento.eva_estado = nuevo_estado
        evaluador_evento.save()

        return JsonResponse({
            'success': True,
            'mensaje': f'Estado actualizado a {nuevo_estado}'
        })
    except EvaluadoresEventos.DoesNotExist:
        return JsonResponse({'success': False, 'mensaje': 'Evaluador no encontrado'}, status=404)
