from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from collections import defaultdict
from app_eventos.models import Eventos
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

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