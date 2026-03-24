from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from collections import defaultdict
from app_eventos.models import Eventos, EvaluadoresEventos, AsistentesEventos, ParticipantesEventos
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import redirect
from django.urls import reverse
from app_areas.models import Areas
from app_categorias.models import Categorias
from django.utils import timezone


def crear_area(request):
    if request.method == "POST":
        nombre = request.POST.get("are_nombre")
        descripcion = request.POST.get("are_descripcion")
        Areas.objects.create(are_nombre=nombre, are_descripcion=descripcion)
        messages.success(request, "Área creada exitosamente.")
    return redirect("super_admin:index_super_admin")

def crear_categoria(request):
    if request.method == "POST":
        nombre = request.POST.get("cat_nombre")
        descripcion = request.POST.get("cat_descripcion")
        area_id = request.POST.get("cat_area_fk")
        area = Areas.objects.get(id=area_id)
        Categorias.objects.create(cat_nombre=nombre, cat_descripcion=descripcion, cat_area_fk=area)
        messages.success(request, "Categoría creada exitosamente.")
    return redirect("super_admin:index_super_admin")

@login_required(login_url='login')  # Protege la vista para usuarios logueados
def index(request):
    eventos = Eventos.objects.all().select_related('eve_administrador_fk')
    eventos_por_estado = defaultdict(list)
    areas = Areas.objects.all()

    # Traer eventos (ejemplo, adáptalo a tu lógica)
    eventos = Eventos.objects.all()
    for evento in eventos:
        # Normaliza el estado
        estado = evento.eve_estado.capitalize()
        eventos_por_estado[estado].append(evento)

    # Cuenta los eventos pendientes
    pendientes_count = len(eventos_por_estado['Pendiente'])

    context = {
        'eventos': eventos,
        'eventos_por_estado': eventos_por_estado,
        'pendientes_count': pendientes_count,
        'areas': areas, 
    }
    return render(request, 'app_super_admin/inicio_super_admin.html', context)

@login_required(login_url='login')  # Protege la vista para usuarios logueados
def ver_evento_adm(request, evento_id):

    evento = get_object_or_404(
        Eventos.objects.select_related('eve_administrador_fk'),
        id=evento_id,
    )
    if evento.eve_imagen:
        evento.imagen_url = request.build_absolute_uri(evento.eve_imagen.url)
    else:
        evento.imagen_url = None

    context = {'evento': evento}
    return render(request, 'app_super_admin/detalle_evento.html', context)

login_required(login_url='login')  # Protege la vista para usuarios logueados
def modificar_estado_evento(request, evento_id, nuevo_estado):
    evento = get_object_or_404(Eventos, pk=evento_id)
    evento.eve_estado = nuevo_estado
    evento.save()
    # Redirigir con parámetro GET
    url = reverse('super_admin:index_super_admin') + '?modal_evento_activo=true'
    return redirect(url)

@login_required(login_url='login')
def editar_perfil(request):
    user = request.user

    if request.method == 'POST':
        try:
            # Solo actualizar campos si están presentes en el POST
            if 'first_name' in request.POST:
                user.first_name = request.POST.get('first_name', '')
            if 'last_name' in request.POST:
                user.last_name = request.POST.get('last_name', '')
            if 'username' in request.POST:
                nuevo_username = request.POST.get('username', '')
                if nuevo_username != user.username:
                    # Verificar unicidad del username
                    if Usuario.objects.filter(username=nuevo_username).exclude(id=user.id).exists():
                        messages.error(request, 'El nombre de usuario ya está en uso.')
                        return redirect('super_admin:index_super_admin')
                    user.username = nuevo_username
            if 'email' in request.POST:
                nuevo_email = request.POST.get('email', '')
                if nuevo_email != user.email:
                    # Verificar unicidad del email
                    if Usuario.objects.filter(email=nuevo_email).exclude(id=user.id).exists():
                        messages.error(request, 'El correo electrónico ya está en uso.')
                        return redirect('super_admin:index_super_admin')
                    user.email = nuevo_email

            # Campos adicionales del modelo Usuario
            if 'segundo_nombre' in request.POST:
                user.segundo_nombre = request.POST.get('segundo_nombre', '')
            if 'segundo_apellido' in request.POST:
                user.segundo_apellido = request.POST.get('segundo_apellido', '')
            if 'telefono' in request.POST:
                user.telefono = request.POST.get('telefono', '')
            
            # Manejo seguro de fecha de nacimiento
            if 'fecha_nacimiento' in request.POST:
                fecha_nacimiento_str = request.POST.get('fecha_nacimiento', '')
                if fecha_nacimiento_str:
                    try:
                        # Validar formato de fecha
                        fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
                        user.fecha_nacimiento = fecha_nacimiento
                    except ValueError:
                        messages.error(request, 'Formato de fecha inválido. Use YYYY-MM-DD.')
                        return redirect('super_admin:index_super_admin')
                else:
                    # Si se envía vacío, establecer como None
                    user.fecha_nacimiento = None

            # Manejo de cambio de contraseña
            current_password = request.POST.get('current_password', '')
            if current_password:
                if user.check_password(current_password):
                    new_password = request.POST.get('new_password', '')
                    confirm_password = request.POST.get('confirm_password', '')
                    
                    if new_password and confirm_password and new_password == confirm_password:
                        if len(new_password) >= 8:  # Validar longitud mínima
                            user.set_password(new_password)
                            update_session_auth_hash(request, user)  # Mantener sesión
                            messages.success(request, 'Contraseña actualizada correctamente.')
                        else:
                            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                            return redirect('super_admin:index_super_admin')
                    else:
                        messages.error(request, 'Las contraseñas no coinciden o están vacías.')
                        return redirect('super_admin:index_super_admin')
                else:
                    messages.error(request, 'La contraseña actual es incorrecta.')
                    return redirect('super_admin:index_super_admin')

            user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
        except Exception as e:
            messages.error(request, f'Error inesperado al actualizar perfil: {str(e)}')

    return redirect('super_admin:index_super_admin')

def gestionar_usuarios(request):
    # Todos los administradores actuales (IDs de usuario)
    admins_ids = Administradores.objects.values_list('usuario_id', flat=True)

    # Usuarios que no son superusuario y no están en la tabla Administradores
    usuarios_no_admin = Usuario.objects.exclude(is_superuser=True).exclude(id__in=admins_ids)

    # Usuarios que ya están como administradores
    administradores = Administradores.objects.select_related('usuario')
  # Agregar eventos_creados y cupo_disponible a cada administrador
    for admin in administradores:
        eventos_creados = Eventos.objects.filter(eve_administrador_fk=admin).count()
        admin.eventos_creados = eventos_creados
        if admin.num_eventos == eventos_creados:
            admin.cupo_disponible = "No tiene cupo disponible"
        else:
            admin.cupo_disponible = (admin.num_eventos or 0) - eventos_creados

    return render(request, 'app_super_admin/asignar_nuevo_admin_eventos.html', {
        'usuarios_no_admin': usuarios_no_admin,
        'administradores': administradores,
    })
    
@login_required(login_url='login')  # Protege la vista para usuarios logueados 
def asignar_admin_evento(request):
    usuario_id = request.POST.get('usuario_id')
    eventos_maximos = request.POST.get('eventos')
    fecha_limite = request.POST.get('fecha_limite')
    codigo = request.POST.get('codigo')

    if not all([usuario_id, eventos_maximos, fecha_limite, codigo]):
        return HttpResponseBadRequest("Faltan campos obligatorios.")

    try:
        usuario = Usuario.objects.get(id=usuario_id)

        Administradores.objects.create(
            usuario=usuario,
            num_eventos=int(eventos_maximos),
            tiempo_limite=fecha_limite,
            estado="Creado",
            clave_acceso=codigo
        )

        # Enviar correo
        html_content = render_to_string('app_super_admin/correos/asignar_rol.html', {
            'nombre': usuario.get_full_name(),
            'clave': codigo,
            'fecha_limite': fecha_limite,
            'num_eventos': eventos_maximos,
            'nombre_usuario': usuario.username,
            'año_actual': datetime.now().year,
        })

        subject = 'Asignación de rol como Administrador de Eventos'
        from_email = 'eventsoft3@gmail.com'
        to = [usuario.email]

        msg = EmailMultiAlternatives(subject, '', from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return JsonResponse({"success": True}, content_type="application/json")


    except Usuario.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@login_required(login_url='login')  # Protege la vista para usuarios logueados
def cancelar_administrador(request):
    if request.method == "POST":
        try:
            datos = json.loads(request.body)
            admin_id = datos.get("admin_id")

            admin = Administradores.objects.get(id=admin_id)
            admin.delete()  # O admin.estado = 'Inactivo'; admin.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})

def obtener_estadisticas_evento(request, evento_id):
    asistentes = AsistentesEventos.objects.filter(asi_eve_evento_fk=evento_id, asi_eve_estado = "Admitido").count()
    evaluadores = EvaluadoresEventos.objects.filter(eva_eve_evento_fk=evento_id, eva_estado = "Admitido").count()
    Participantes = ParticipantesEventos.objects.filter(par_eve_evento_fk=evento_id, par_eve_estado = "Admitido").count()
    total_particpantes = asistentes + evaluadores + Participantes
    return JsonResponse({
        'asistentes': asistentes,
        'evaluadores': evaluadores,
        'participantes': Participantes,
        'total_participantes': total_particpantes
    })
    


@login_required(login_url='login')
def cancelar_evento(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    evento.eve_estado = "Cancelado"
    evento.save()
    
    # Redirigir con parámetro GET
    url = reverse('super_admin:index_super_admin') + '?modal_cancelar_evento=true'
    return redirect(url)
 
@login_required(login_url='login')
def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    evento.delete()
    
    # Redirigir con parámetro GET
    url = reverse('super_admin:index_super_admin') + '?modal_eliminado_evento=true'
    return redirect(url)
