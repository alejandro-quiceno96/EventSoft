from django.shortcuts import render,  get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import Asistentes
from app_eventos.models import AsistentesEventos, Eventos, EventosCategorias
from app_categorias.models import Categorias



def inicio_asistente(request):

        try:
            # Buscar al participante por cédula
            asistente = Asistentes.objects.get(usuario=request.user)

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
                    "eve_memorias": evento.eve_memorias
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
    

@login_required(login_url='login')
@csrf_exempt 
def cancelar_inscripcion(request, evento_id, asistente_id):
    if request.method == 'POST':

        if not asistente_id:
            return JsonResponse({"success": False, "error": "ID del participante faltante"}, status=400)

        try:
            asistente_evento = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento_id, asi_eve_asistente_fk=asistente_id).first()
            asistente = Asistentes.objects.get(id=asistente_id)
            
            if asistente_evento:
                # Eliminar archivo de soporte si existe
                if asistente_evento.asi_eve_soporte:
                    default_storage.delete(asistente_evento.asi_eve_soporte.path)
                
                # VERIFICAR ANTES DE ELIMINAR la inscripción
                # Contar cuántas inscripciones tiene este asistente
                inscripciones_count = AsistentesEventos.objects.filter(asi_eve_asistente_fk=asistente_id).count()
                
                # Eliminar la inscripción
                asistente_evento.delete()
                
                # Si era la única inscripción, eliminar el asistente
                if inscripciones_count == 1:  # Era la única inscripción
                    asistente.delete()
                    
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "No se encontró la inscripción"}, status=404)

        except Exception as e:
            print("Error:", e)
            return JsonResponse({"success": False, "error": "Error al procesar la solicitud"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

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
                    return redirect('app_asistente:inicio_asistente')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('app_asistente:inicio_asistente')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('app_asistente:inicio_asistente') # Redirige a la página de inicio del visitante

    return redirect('app_asistente:inicio_asistente')