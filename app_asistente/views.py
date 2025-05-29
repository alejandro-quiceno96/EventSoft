from django.shortcuts import render,  get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import Asistentes
from app_eventos.models import AsistentesEventos, Eventos, EventosCategorias
from app_categorias.models import Categorias

def buscar_asistentes(request):
    return render(request, 'app_asistente/buscar_asistente.html')

def inicio_asistente(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')

        try:
            # Buscar al participante por cédula
            asistente = Asistentes.objects.get(asi_cedula=cedula)

            # Obtener eventos donde el participante está inscrito
            participaciones = AsistentesEventos.objects.filter(
                asi_eve_asistente_fk=asistente
            ).select_related("asi_eve_evento_fk")

            eventos_data = []

            for participacion in participaciones:
                evento = participacion.asi_eve_evento_fk # acceso correcto a la relación
                eventos_data.append({
                    "eve_id": evento.id,
                    "eve_nombre": evento.eve_nombre,
                    "eve_fecha_inicio": evento.eve_fecha_inicio,
                    "eve_fecha_fin": evento.eve_fecha_fin,
                    "eve_imagen": evento.eve_imagen,
                    "asi_eve_estado": participacion.asi_eve_estado,
                })
                

            return render(request, 'app_asistente/eventos_asistentes.html', {
                "eventos": eventos_data,
                "cedula_participante": asistente.id
            })

        except Exception as e:
            print(e)

    # Si no es POST, renderizar formulario o vista vacía
    return render(request, "app_asistente/eventos_asistentes.html", {
        "eventos": [],
        "cedula_participante": None
    })
    
def evento_asistentes(request, evento_id, asistente_id):
    if request.method == 'GET':
        # Obtener el evento o devolver 404
        evento = get_object_or_404(Eventos, id=evento_id)

        # Obtener la clave de acceso si existe
        clave_acceso = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento_id, asi_eve_asistente_fk=asistente_id).first()

        # Convertir el evento a diccionario
        datos_evento = {
            'eve_id': evento.id,
            'eve_nombre': evento.eve_nombre,
            'eve_descripcion': evento.eve_descripcion,
            'eve_ciudad': evento.eve_ciudad,
            'eve_lugar': evento.eve_lugar,
            'eve_fecha_inicio': evento.eve_fecha_inicio,
            'eve_fecha_fin': evento.eve_fecha_fin,
            'eve_imagen': evento.eve_imagen.url if evento.eve_imagen.url else None,
            'eve_cantidad': evento.eve_capacidad if evento.eve_capacidad > 0 else 'Cupos ilimitados',
            'eve_costo': 'Con Pago' if evento.eve_tienecosto == True else "Gratuito",
            'eve_programacion':evento.eve_programacion.url if evento.eve_programacion.url else None,
            'eve_clave_acceso': clave_acceso.asi_eve_clave if clave_acceso else None,
            'codigo_qr': clave_acceso.asi_eve_qr.url if clave_acceso else None,
        }

        # Obtener categoría si existe
        evento_categoria = EventosCategorias.objects.get(eve_cat_evento_fk=evento_id)
        categoria = Categorias.objects.get(id=evento_categoria.eve_cat_categoria_fk.id)
        categoria_nombre = categoria.cat_nombre

        datos_evento['eve_categoria'] = categoria_nombre if categoria else None

        return JsonResponse(datos_evento, safe=False)
    
def obtener_asistente(request, asistentes_id):
    asistente = get_object_or_404(Asistentes, id= asistentes_id)
    
    if asistente:
            datos = {
                "asi_id": asistente.id,
                "asi_nombre": asistente.asi_nombre,
                "asi_correo":asistente.asi_correo,
                "asi_telefono": asistente.asi_telefono,
            }
            return JsonResponse(datos)
    else:
            return JsonResponse({"error": "No se encontró la información"}, status=404)

@csrf_exempt
def modificar_asistente(request, asistente_id):
    
    if request.method == "POST":
        nombre = request.POST.get("par_nombre")
        correo = request.POST.get("par_correo")
        telefono = request.POST.get("par_telefono")

        try:
            asistente = Asistentes.objects.get(id=asistente_id)
        except Asistentes.DoesNotExist:
            return JsonResponse({"success": False, "error": "Participante no encontrado"})

        asistente.asi_nombre = nombre
        asistente.asi_correo = correo
        asistente.telefono = telefono
        asistente.save()

        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

@csrf_exempt 
def cancelar_inscripcion(request, evento_id, asistente_id):
    if request.method == 'POST':

        if not asistente_id:
            return JsonResponse({"success": False, "error": "ID del participante faltante"}, status=400)

        try:
            # Buscar la inscripción en la tabla 'participantes_eventos'
            asistente_evento = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento_id, asi_eve_asistente_fk=asistente_id).first()

            if asistente_evento:
                # Eliminar el documento asociado si existe
                if asistente_evento.asi_eve_soporte:
                    # Eliminar el archivo físico de la carpeta media
                    default_storage.delete(asistente_evento.asi_eve_soporte.path)
                
                # Eliminar la inscripción
                asistente_evento.delete()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "No se encontró la inscripción"}, status=404)

        except Exception as e:
            print("Error:", e)
            return JsonResponse({"success": False, "error": "Error al procesar la solicitud"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
