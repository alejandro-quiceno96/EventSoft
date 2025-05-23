from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from .models import AdministradorEvento, Evento  # Asumiendo que tienes un modelo Evento

@require_http_methods(["GET", "POST"])
def inicio_sesion_administrador(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        
        try:
            # Utilizando Django ORM para obtener el administrador por la cédula
            administrador = AdministradorEvento.objects.get(id=cedula)
            
            # Guardando datos en la sesión
            request.session['usuario'] = cedula
            request.session['administrador_id'] = administrador.id
            request.session['administrador_nombre'] = administrador.nombre
            
            messages.success(request, '✅ Inicio de sesión exitoso.')
            return redirect('administrador:inicio')  # namespace:view_name
            
        except AdministradorEvento.DoesNotExist:
            messages.error(request, '❌ Cédula no registrada.')
    
    return render(request, 'administrador/inicio_sesion.html')

def obtener_eventos():
    """Función para obtener todos los eventos"""
    return Evento.objects.all()

def inicio(request):
    """Vista para la administración de eventos"""
    eventos = obtener_eventos()
    administrador_nombre = request.session.get('administrador_nombre')
    
    context = {
        'eventos': eventos,
        'administrador': administrador_nombre
    }
    
    return render(request, 'administrador/admin.html', context)