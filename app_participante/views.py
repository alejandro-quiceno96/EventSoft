from django.shortcuts import render, redirect, get_object_or_404
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

@csrf_exempt
def info_participantes_eventos(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')

        try:
            # Buscar al participante por cédula
            participante = Participantes.objects.get(par_cedula=cedula)

            # Obtener eventos donde el participante está inscrito
            participaciones = ParticipantesEventos.objects.filter(
                par_eve_participante_fk=participante
            ).select_related("par_eve_evento_fk")

            eventos_data = []

            for participacion in participaciones:
                evento = participacion.par_eve_evento_fk  # acceso correcto a la relación

                # Obtener criterios y calificaciones del evento
                criterios = Criterios.objects.filter(cri_evento_fk=evento)
                calificaciones = Calificaciones.objects.filter(
                    clas_participante_fk=participante,
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
                    "calificacion": round(promedio, 2) if promedio is not None else "Sin calificar"
                })

            return render(request, 'app_participantes/eventos_participante.html', {
                "eventos": eventos_data,
                "cedula_participante": participante.id
            })

        except Participantes.DoesNotExist:
            return render(request, "app_participantes/eventos_participante.html", {
                "eventos": [],
                "cedula_participante": cedula,
                "error": "Participante no encontrado."
            })

        except Exception as e:
            print(e)

    # Si no es POST, renderizar formulario o vista vacía
    return render(request, "app_participantes/eventos_participante.html", {
        "eventos": [],
        "cedula_participante": None
    })

def buscar_participantes(request):
    # Renderizar la plantilla con el contexto
    return render(request, 'app_participantes/buscar_participantes.html')


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
        'cedula': participante_id
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
def obtener_datos_participante(request, participante_id,evento_id, ):

    try:
        if participante_id is None:
            return JsonResponse({"error": "Falta el parámetro 'participante_id'"}, status=400)

        # Buscar la relación del participante en el evento
        participante_evento = ParticipantesEventos.objects.filter(
            par_eve_participante_fk=participante_id, par_eve_evento_fk=evento_id
        ).select_related('par_eve_participante_fk').first()

        if participante_evento:
            # Obtener los datos del participante relacionados
            participante = participante_evento.par_eve_participante_fk
            datos = {
                "par_id": participante.id,
                "par_nombre": participante.par_nombre,
                "par_correo": participante.par_correo,
                "par_telefono": participante.par_telefono,
                "par_eve_evento_fk": participante_evento.par_eve_documentos.url
            }
            return JsonResponse(datos)
        else:
            return JsonResponse({"error": "No se encontró la información"}, status=404)

    except Exception as e:
        return JsonResponse({"error": f"Error en el servidor: {str(e)}"}, status=500)
    
@csrf_exempt
def modificar_inscripcion(request, evento_id, participante_id):
    if request.method == 'POST':
        nombre = request.POST.get("par_nombre")
        correo = request.POST.get("par_correo")
        telefono = request.POST.get("par_telefono")
        documento = request.FILES.get("par_eve_documentos")

        try:
            # 1. Obtener el participante utilizando ORM
            participante = Participantes.objects.filter(id=participante_id).first()

            if not participante:
                return JsonResponse({"success": False, "error": "Participante no encontrado"})

            # 2. Actualizar los datos del participante
            participante.par_nombre = nombre
            participante.par_correo = correo
            participante.par_telefono = telefono
            participante.save()

            # 3. Si se sube un documento, actualizarlo en 'ParticipanteEvento'
            if documento:
                participante_evento = ParticipantesEventos.objects.filter(par_eve_participante_fk=participante_id, par_eve_evento_fk=evento_id).first()
                
                if participante_evento:
                    # Eliminar el documento anterior si existe
                    if participante_evento.par_eve_documentos:
                        default_storage.delete(participante_evento.par_eve_documentos.path)
                        participante_evento.par_eve_documentos.delete(save=False)

                    # Actualizar el campo de documentos en el modelo ParticipanteEvento
                    participante_evento.par_eve_documentos = documento
                    participante_evento.save()
                else:
                    return JsonResponse({"success": False, "error": "Inscripción al evento no encontrada"})


            return JsonResponse({"success": True})

        except Exception as e:
            print("Error al modificar inscripción:", e)
            return JsonResponse({"success": False, "error": str(e)})
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    
@csrf_exempt 
def cancelar_inscripcion(request, evento_id, participante_id):
    if request.method == 'POST':

        if not participante_id:
            return JsonResponse({"success": False, "error": "ID del participante faltante"}, status=400)

        try:
            # Buscar la inscripción en la tabla 'participantes_eventos'
            participante_evento = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento_id, par_eve_participante_fk=participante_id).first()

            if participante_evento:
                # Eliminar el documento asociado si existe
                if participante_evento.par_eve_documentos:
                    # Eliminar el archivo físico de la carpeta media
                    default_storage.delete(participante_evento.par_eve_documentos.path)
                
                # Eliminar la inscripción
                participante_evento.delete()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "No se encontró la inscripción"}, status=404)

        except Exception as e:
            print("Error:", e)
            return JsonResponse({"success": False, "error": "Error al procesar la solicitud"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)