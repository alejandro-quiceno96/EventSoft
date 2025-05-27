from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import Http404
from collections import defaultdict
from app_eventos.models import Eventos, EventosCategorias, AsistentesEventos, ParticipantesEventos
from app_administrador.models import Administradores


def index(request):
    eventos = Eventos.objects.select_related('eve_administrador_fk').all()
    eventos_creados = Eventos.objects.filter(eve_estado='Creado').all()
    eventos_por_estado = defaultdict(list)
    for evento in eventos_creados:
        eventos_por_estado[evento.eve_estado].append(evento)
    context = {
        'eventos': eventos,
        'eventos_por_estado': eventos_por_estado,
    }
    return render(request, 'app_super_admin/inicio_super_admin.html', context)


def ver_evento_adm(request, evento_id):
    """Vista para ver detalles de un evento específico"""
    evento = get_object_or_404(Eventos, id=evento_id)
    evento.imagen_url = evento.eve_imagen.url if evento.eve_imagen else None
    context = {'evento': evento}
    return render(request, 'app_super_admin/detalle_evento.html', context)


def inicio_sesion_super_admin(request):
    """Vista para el inicio de sesión del super administrador"""
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