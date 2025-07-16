from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from collections import defaultdict
from app_eventos.models import Eventos
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from datetime import datetime

@login_required(login_url='login')  # Protege la vista para usuarios logueados
def index(request):
    eventos = Eventos.objects.all().select_related('eve_administrador_fk')
    eventos_por_estado = defaultdict(list)
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
    return redirect('super_admin:index_super_admin')

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
                    return redirect('super_admin:index_super_admin')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('super_admin:index_super_admin')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('super_admin:index_super_admin')

    return redirect('super_admin:index_super_admin')  # Redirige a la página de inicio si no es POST

def gestionar_usuarios(request):
    # Todos los administradores actuales (IDs de usuario)
    admins_ids = Administradores.objects.values_list('usuario_id', flat=True)

    # Usuarios que no son superusuario y no están en la tabla Administradores
    usuarios_no_admin = Usuario.objects.exclude(is_superuser=True).exclude(id__in=admins_ids)

    # Usuarios que ya están como administradores
    administradores = Administradores.objects.select_related('usuario')

    return render(request, 'app_super_admin/asignar_nuevo_admin_eventos.html', {
        'usuarios_no_admin': usuarios_no_admin,
        'administradores': administradores,
    })
    
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

