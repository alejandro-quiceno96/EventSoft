from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from collections import defaultdict
from app_eventos.models import Eventos
from app_administrador.models import Administradores

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

def inicio_sesion_super_admin(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        try:
            administrador = Administradores.objects.get(id=cedula)
            request.session['administrador'] = {
                'id': administrador.id,
                'nombre': administrador.adm_nombre,
            }
            messages.success(request, '✅ Inicio de sesión exitoso.')
            return redirect('super_admin:index')
        except Administradores.DoesNotExist:
            messages.error(request, '❌ Cédula no registrada.')
    return render(request, 'app_super_admin/inicio_sesion.html')

def modificar_estado_evento(request, evento_id, nuevo_estado):
    evento = get_object_or_404(Eventos, pk=evento_id)
    evento.eve_estado = nuevo_estado
    evento.save()
    return redirect('super_admin:index')