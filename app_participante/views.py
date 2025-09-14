from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime
from app_eventos.models import ParticipantesEventos
from app_participante.models import Participantes
from django.http import JsonResponse, Http404, HttpResponse
from weasyprint import HTML
from app_eventos.models import Eventos, EventosCategorias
from app_evaluador.models import Calificaciones
from app_criterios.models import Criterios
from app_categorias.models import Categorias
from django.core.files.storage import default_storage
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages 


@csrf_exempt
@login_required(login_url='login')
def info_participantes_eventos(request):
    try:
        # Buscar al participante por cédula
        participante = ParticipantesEventos.objects.get(par_eve_participante_fk__usuario=request.user)

        # Obtener calificaciones del participante
        comentarios = Calificaciones.objects.filter(clas_proyecto_fk=participante.par_eve_proyecto).select_related('cal_evaluador_fk')
        # Obtener eventos donde el participante está inscrito
        participaciones = ParticipantesEventos.objects.filter(
            par_eve_participante_fk=participante.par_eve_participante_fk
        ).select_related("par_eve_evento_fk")

        eventos_data = []

        for participacion in participaciones:
            evento = participacion.par_eve_evento_fk  # acceso correcto a la relación

            # Obtener criterios y calificaciones del evento
            criterios = Criterios.objects.filter(cri_evento_fk=evento)
            calificaciones = Calificaciones.objects.filter(
                clas_proyecto_fk=participante.par_eve_proyecto,
                cal_criterio_fk__in=criterios
            )

            total_peso = 0
            total_valor = 0

            for criterio in criterios:
                calificaciones_criterio = calificaciones.filter(cal_criterio_fk=criterio)
                if calificaciones_criterio.exists():
                    promedio_criterio = sum(c.cal_valor for c in calificaciones_criterio) / calificaciones_criterio.count()
                    total_peso += criterio.cri_peso
                    total_valor += promedio_criterio * criterio.cri_peso

            promedio = (total_valor / total_peso) if total_peso > 0 else None

            eventos_data.append({
                "eve_id": evento.id,
                "eve_nombre": evento.eve_nombre,
                "eve_fecha_inicio": evento.eve_fecha_inicio,
                "eve_fecha_fin": evento.eve_fecha_fin,
                "eve_imagen": evento.eve_imagen,
                "par_eve_estado": participacion.par_eve_estado,
                "calificacion": round(promedio, 2) if promedio is not None else "Sin calificar",
                "comentarios": comentarios,
                "eve_memorias": evento.eve_memorias,

            })
            
        
        # Ordenar eventos por fecha de inicio
        return render(request, 'app_participantes/eventos_participante.html', {
            "eventos": eventos_data,
            "cedula_participante": participante.par_eve_participante_fk.id,
        })

    except Exception as e:
        print(e)
        return render(request, 'app_participantes/eventos_participante.html', {
            "eventos":  [],
            "cedula_participante": None
        })




login_required(login_url='login')
def evento_detalle_participante(request, evento_id, participante_id):
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
    
    #Obtener Clave de acceso 

    try:
        clave_acceso = get_object_or_404(
            ParticipantesEventos,
            par_eve_evento_fk=evento_id,
            par_eve_participante_fk=participante_id
        )
        
    except (ParticipantesEventos.DoesNotExist):
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
        'eve_cantidad': evento.eve_capacidad if evento.eve_capacidad is not None else 'Cupos ilimitados',
        'eve_costo':'Con Pago' if evento.eve_tienecosto else 'Sin Pago',
        'eve_programacion': evento.eve_programacion.url if evento.eve_programacion else None,
        'eve_categoria': categoria_nombre,
        'eve_clave': clave_acceso.par_eve_clave,
        'codigo_qr': clave_acceso.par_eve_qr.url,
        'cedula': participante_id,
        "eve_informacion_tecnica": evento.eve_informacion_tecnica.url if evento.eve_informacion_tecnica else None,
        'proyecto': clave_acceso.par_eve_proyecto.pro_codigo if clave_acceso.par_eve_proyecto else 'No asignado',
        
        
    }

    return JsonResponse(datos_evento)


def generar_pdf_criterios(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    criterios = Criterios.objects.filter(cri_evento_fk=evento)

    html_string = render(request, 'app_participantes/pdf_criterios.html', {
        'criterios': criterios,
        'evento': evento,
    }).content.decode('utf-8')  # Obtener string HTML

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=criterios_evaluacion_{evento.eve_nombre}.pdf'
    return response

@csrf_exempt
@login_required(login_url='login')
def obtener_datos_participante(request, participante_id, evento_id):
    try:
        if participante_id is None:
            return JsonResponse({"error": "Falta el parámetro 'participante_id'"}, status=400)

        # Relación participante-evento
        participante_evento = ParticipantesEventos.objects.filter(
            par_eve_participante_fk=participante_id, 
            par_eve_evento_fk=evento_id
        ).select_related('par_eve_proyecto').first()

        if participante_evento:
            proyecto = participante_evento.par_eve_proyecto
            datos = {
                "nombre": proyecto.pro_nombre,
                "descripcion": proyecto.pro_descripcion,
                "documento": proyecto.pro_documentos.url if proyecto.pro_documentos else None
            }
            return JsonResponse(datos)
        else:
            return JsonResponse({"error": "No se encontró la información"}, status=404)

    except Exception as e:
        return JsonResponse({"error": f"Error en el servidor: {str(e)}"}, status=500)

    
@csrf_exempt
def modificar_inscripcion(request, evento_id, participante_id):
    if request.method == 'POST':
        try:
            # 1. Obtener participante desde el usuario logueado
            participante = Participantes.objects.filter(usuario=request.user).first()
            if not participante:
                return JsonResponse({"success": False, "error": "Participante no encontrado"})

            # 2. Obtener inscripción en el evento
            participante_evento = ParticipantesEventos.objects.filter(
                par_eve_participante_fk=participante_id,
                par_eve_evento_fk=evento_id
            ).first()

            if not participante_evento:
                return JsonResponse({"success": False, "error": "Inscripción al evento no encontrada"})

            # 3. Obtener el proyecto relacionado
            proyecto = participante_evento.par_eve_proyecto
            if not proyecto:
                return JsonResponse({"success": False, "error": "El participante no tiene proyecto asociado"})

            # 4. Si se sube un nuevo documento, reemplazar
            documento = request.FILES.get("par_eve_documentos")
            if documento:
                if proyecto.pro_documentos:
                    proyecto.pro_documentos.delete(save=False)  # Elimina archivo viejo
                proyecto.pro_documentos = documento

            # 5. Actualizar otros datos
            nombre = request.POST.get("pro_nombre")
            descripcion = request.POST.get("pro_descripcion")

            if nombre:
                proyecto.pro_nombre = nombre
            if descripcion:
                proyecto.pro_descripcion = descripcion

            proyecto.save()

            return JsonResponse({"success": True})

        except Exception as e:
            print("Error al modificar inscripción:", e)
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    
@login_required(login_url='login')  # Protege la vista para usuarios logueados
@csrf_exempt 
def cancelar_inscripcion(request, evento_id, participante_id):
    """
    Vista para cancelar la inscripción de un participante a un evento
    """
    if request.method == 'POST':
        
        # Validar que se proporcione el ID del participante
        if not participante_id:
            return JsonResponse({
                "success": False, 
                "error": "ID del participante faltante"
            }, status=400)

        try:
            # Buscar la inscripción en la tabla 'participantes_eventos'
            participante_evento = ParticipantesEventos.objects.filter(
                par_eve_evento_fk=evento_id, 
                par_eve_participante_fk=participante_id
            ).first()
            
            if not participante_evento:
                return JsonResponse({
                    "success": False, 
                    "error": "No se encontró la inscripción"
                }, status=404)
            
            # Obtener el participante
            participante = Participantes.objects.get(id=participante_id)
            
            # Verificar cuántas inscripciones tiene este participante ANTES de eliminar
            total_inscripciones = ParticipantesEventos.objects.filter(
                par_eve_participante_fk=participante_id
            ).count()
            
            # Eliminar el documento asociado si existe
            if participante_evento.par_eve_documentos:
                try:
                    # Eliminar el archivo físico de la carpeta media
                    default_storage.delete(participante_evento.par_eve_documentos.path)
                except Exception as e:
                    print(f"Error al eliminar archivo: {e}")
                    # Continuar aunque falle la eliminación del archivo
            
            # Eliminar la inscripción
            proyecto = participante_evento.par_eve_proyecto
            proyecto.delete()  # Eliminar el proyecto asociado
            participante_evento.delete()
            
            # Si era la única inscripción, eliminar el participante
            if total_inscripciones == 1:
                participante.delete()
                
            return JsonResponse({"success": True})

        except Participantes.DoesNotExist:
            return JsonResponse({
                "success": False, 
                "error": "Participante no encontrado"
            }, status=404)
            
        except Exception as e:
            print(f"Error al cancelar inscripción: {e}")
            return JsonResponse({
                "success": False, 
                "error": "Error al procesar la solicitud"
            }, status=500)
            
    else:
        return JsonResponse({
            "success": False, 
            "error": "Método no permitido"
        }, status=405)

def generar_pdf_comentarios_participante(request, evento_id):
    """
    Vista para descargar PDF con las calificaciones de un participante usando WeasyPrint
    """
    # Obtener el participante
    participante = get_object_or_404(ParticipantesEventos, par_eve_participante_fk__usuario=request.user)
    
    # Obtener todas las calificaciones del participante
    calificaciones = Calificaciones.objects.filter(
        clas_proyecto_fk=participante.par_eve_proyecto
    ).select_related(
        'cal_evaluador_fk__usuario',
        'cal_criterio_fk'
    ).order_by('cal_evaluador_fk', 'cal_criterio_fk')
    
    # Agrupar calificaciones por evaluador
    evaluadores_data = {}
    criterios_pesos = {}
    
    for calificacion in calificaciones:
        evaluador = calificacion.cal_evaluador_fk
        criterio = calificacion.cal_criterio_fk
        
        # Guardar pesos de criterios para cálculo final
        criterios_pesos[criterio.id] = criterio.cri_peso
        
        if evaluador.id not in evaluadores_data:
            evaluadores_data[evaluador.id] = {
                'evaluador':  evaluador,
                'calificaciones': []
            }
        
        evaluadores_data[evaluador.id]['calificaciones'].append(calificacion)
    
    try:
        participante_evento = ParticipantesEventos.objects.get(
            par_eve_participante_fk=participante.par_eve_participante_fk,
            par_eve_evento_fk=evento_id
        )
        nota_final = participante_evento.par_eve_calificacion_final
    except ParticipantesEventos.DoesNotExist:
        nota_final = None  # o lo que desees manejar en caso de que no exista
    
    expositores = ParticipantesEventos.objects.filter(par_eve_proyecto=participante.par_eve_proyecto)
    nombres_expositores = [
            f"{exp.par_eve_participante_fk.usuario.first_name} {exp.par_eve_participante_fk.usuario.last_name}"
            for exp in expositores
        ]
    
    # Preparar contexto para el template
    context = {
        'expositores': nombres_expositores,
        'evaluadores_data': evaluadores_data,
        'nota_final': nota_final,
        'fecha_reporte': datetime.now(),
        'tiene_calificaciones': calificaciones.exists(),
        'proyecto': participante.par_eve_proyecto,
    }
    
    # Renderizar HTML
    html_string = render_to_string('app_participantes/comentarios_pdf.html', context)
    
    # Crear el PDF
    html = HTML(string=html_string)
    
    # Crear el response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="calificaciones_{participante.par_eve_participante_fk.usuario.documento_identidad}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    # Generar PDF y escribir al response
    html.write_pdf(response)
    
    return response

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
                    return redirect('app_participante:ver_info_participante')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('app_participante:ver_info_participante')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('app_participante:ver_info_participante') # Redirige a la página de inicio del visitante

    return redirect('app_participante:ver_info_participante')  # Redirige a la página de inicio del visitante si no es una solicitud POST