from django.shortcuts import render,  get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import Asistentes
from app_eventos.models import AsistentesEventos, Eventos, EventosCategorias
from app_usuarios.models import Usuario
from django.db import IntegrityError
from datetime import datetime
import os


def inicio_asistente(request):
    # Verificar si el usuario está autenticado
    if not request.user.is_authenticated:
        return render(request, "app_asistente/eventos_asistentes.html", {
            "eventos": [],
            "cedula_participante": None
        })

    try:
        # Buscar al asistente por usuario (usuario autenticado)
        asistente = Asistentes.objects.get(usuario=request.user)

        # Obtener eventos donde el asistente está inscrito
        participaciones = AsistentesEventos.objects.filter(
            asi_eve_asistente_fk=asistente
        ).select_related("asi_eve_evento_fk")

        eventos_data = []

        for participacion in participaciones:
            evento = participacion.asi_eve_evento_fk
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

    except Asistentes.DoesNotExist:
        # El usuario está autenticado pero no tiene perfil de asistente
        return render(request, "app_asistente/eventos_asistentes.html", {
            "eventos": [],
            "cedula_participante": None
        })
    except Exception as e:
        # Log del error para debugging
        print(f"Error en inicio_asistente: {e}")
        return render(request, "app_asistente/eventos_asistentes.html", {
            "eventos": [],
            "cedula_participante": None
        })
    
def evento_asistentes(request, evento_id, asistente_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el evento o devolver 404
        evento = get_object_or_404(Eventos, id=evento_id)

        # Obtener la clave de acceso si existe
        clave_acceso = AsistentesEventos.objects.filter(
            asi_eve_evento_fk=evento_id, 
            asi_eve_asistente_fk=asistente_id
        ).first()

        # Convertir el evento a diccionario
        datos_evento = {
            'eve_id': evento.id,
            'eve_nombre': evento.eve_nombre,
            'eve_descripcion': evento.eve_descripcion,
            'eve_ciudad': evento.eve_ciudad,
            'eve_lugar': evento.eve_lugar,
            'eve_fecha_inicio': evento.eve_fecha_inicio,
            'eve_fecha_fin': evento.eve_fecha_fin,
            'eve_imagen': evento.eve_imagen if evento.eve_imagen else None,
            'eve_cantidad': evento.eve_capacidad if evento.eve_capacidad > 0 else 'Cupos ilimitados',
            'eve_costo': 'Con Pago' if evento.eve_tienecosto else "Gratuito",
            'eve_programacion': evento.eve_programacion if evento.eve_programacion else None,
            'eve_clave_acceso': clave_acceso.asi_eve_clave if clave_acceso else None,
            'codigo_qr': clave_acceso.asi_eve_qr if clave_acceso and clave_acceso.asi_eve_qr else None,
        }

        # Obtener categoría si existe (manejar caso de no existencia)
        try:
            evento_categoria = EventosCategorias.objects.get(eve_cat_evento_fk=evento_id)
            categoria = evento_categoria.eve_cat_categoria_fk
            datos_evento['eve_categoria'] = categoria.cat_nombre
        except EventosCategorias.DoesNotExist:
            datos_evento['eve_categoria'] = None

        return JsonResponse(datos_evento, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)
    

@login_required(login_url='login')
@csrf_exempt 
def cancelar_inscripcion(request, evento_id, asistente_id):
    if request.method == 'POST':
        # VERIFICACIÓN DE PERMISOS - IMPORTANTE AÑADIR
        try:
            asistente = Asistentes.objects.get(id=asistente_id)
            if request.user != asistente.usuario:
                return JsonResponse({"success": False, "error": "No autorizado"}, status=403)
        except Asistentes.DoesNotExist:
            return JsonResponse({"success": False, "error": "Asistente no encontrado"}, status=404)

        if not asistente_id:
            return JsonResponse({"success": False, "error": "ID del asistente faltante"}, status=400)

        try:
            asistente_evento = AsistentesEventos.objects.filter(
                asi_eve_evento_fk=evento_id, 
                asi_eve_asistente_fk=asistente_id
            ).first()
            
            if asistente_evento:
                # Los archivos de soporte y QR ahora están en Supabase, por lo que no los eliminamos localmente.
                # VERIFICAR ANTES DE ELIMINAR la inscripción
                inscripciones_count = AsistentesEventos.objects.filter(
                    asi_eve_asistente_fk=asistente_id
                ).count()
                
                # Eliminar la inscripción
                asistente_evento.delete()
                
                # MEJORA: Eliminar asistente si era la única inscripción
                if inscripciones_count == 1:  # Era la única inscripción
                    # Eliminar también el usuario asociado
                    asistente.delete()
                    
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "No se encontró la inscripción"}, status=404)

        except Exception as e:
            print("Error:", e)
            return JsonResponse({"success": False, "error": "Error al procesar la solicitud"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)



@login_required(login_url='login')
def editar_perfil(request):
    user = request.user

    if request.method == 'POST':
        try:
            # Campos básicos - solo actualizar si tienen valor
            if request.POST.get('first_name') is not None:
                user.first_name = request.POST.get('first_name', '')
            if request.POST.get('last_name') is not None:
                user.last_name = request.POST.get('last_name', '')
            
            # Validar unicidad del username
            nuevo_username = request.POST.get('username', '')
            if nuevo_username and nuevo_username != user.username:
                if Usuario.objects.filter(username=nuevo_username).exclude(id=user.id).exists():
                    messages.error(request, 'El nombre de usuario ya está en uso.')
                    return redirect('app_asistente:inicio_asistente')
                user.username = nuevo_username
            
            # Validar unicidad del email
            nuevo_email = request.POST.get('email', '')
            if nuevo_email and nuevo_email != user.email:
                if Usuario.objects.filter(email=nuevo_email).exclude(id=user.id).exists():
                    messages.error(request, 'El correo electrónico ya está en uso.')
                    return redirect('app_asistente:inicio_asistente')
                user.email = nuevo_email

            # Campos adicionales del modelo Usuario
            if request.POST.get('segundo_nombre') is not None:
                user.segundo_nombre = request.POST.get('segundo_nombre', '')
            if request.POST.get('segundo_apellido') is not None:
                user.segundo_apellido = request.POST.get('segundo_apellido', '')
            if request.POST.get('telefono') is not None:
                user.telefono = request.POST.get('telefono', '')
            
            # Manejo seguro de fecha de nacimiento
            fecha_nacimiento_str = request.POST.get('fecha_nacimiento', '')
            if fecha_nacimiento_str:
                try:
                    # Validar formato de fecha
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
                    user.fecha_nacimiento = fecha_nacimiento
                except ValueError:
                    messages.error(request, 'Formato de fecha inválido. Use YYYY-MM-DD.')
                    return redirect('app_asistente:inicio_asistente')
            elif request.POST.get('fecha_nacimiento') is not None:
                # Si se envía vacío, establecer como None
                user.fecha_nacimiento = None

            # Manejo de cambio de contraseña
            current_password = request.POST.get('current_password', '')
            if current_password:
                # Validar contraseña actual
                if not user.check_password(current_password):
                    messages.error(request, 'La contraseña actual es incorrecta.')
                    return redirect('app_asistente:inicio_asistente')
                
                new_password = request.POST.get('new_password', '')
                confirm_password = request.POST.get('confirm_password', '')
                
                # Validar nuevas contraseñas
                if not new_password or not confirm_password:
                    messages.error(request, 'Las nuevas contraseñas no pueden estar vacías.')
                    return redirect('app_asistente:inicio_asistente')
                
                if new_password != confirm_password:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return redirect('app_asistente:inicio_asistente')
                
                if len(new_password) < 8:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                    return redirect('app_asistente:inicio_asistente')
                
                # Cambiar contraseña
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # Mantener sesión
                messages.success(request, 'Contraseña actualizada correctamente.')

            # Guardar cambios
            user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            
        except IntegrityError as e:
            messages.error(request, 'Error de integridad de datos. Puede que el nombre de usuario o email ya estén en uso.')
        except Exception as e:
            messages.error(request, f'Error inesperado al actualizar perfil: {str(e)}')

    # Redirigir siempre a la página de inicio del asistente
    return redirect('app_asistente:inicio_asistente')




