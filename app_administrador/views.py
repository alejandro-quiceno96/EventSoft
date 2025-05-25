from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime

from app_eventos.models import Eventos, EventosCategorias, ParticipantesEventos, AsistentesEventos
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_administrador.models import Administradores


# Obtener áreas disponibles
def obtener_areas_eventos():
    return Areas.objects.all()

# Obtener categorías por área (AJAX)
@require_http_methods(["GET"])
def get_categorias(request, area_id):
    try:
        categorias = Categorias.objects.filter(cat_area_fk=area_id)
        resultado = [{'cat_codigo': c.id, 'cat_nombre': c.cat_nombre} for c in categorias]
        return JsonResponse(resultado, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener categorías: {str(e)}'}, status=500)

# Crear un nuevo evento
@csrf_exempt
@require_http_methods(["GET", "POST"])
def crear_evento(request):
    if request.method == 'POST':
        try:
            # Datos del formulario
            nombre = request.POST.get('nombre_evento')
            descripcion = request.POST.get('descripcion_evento')
            ciudad = request.POST.get('ciudad')
            lugar = request.POST.get('lugar')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            categoria = request.POST.get('categoria')
            inscripcion = request.POST.get('inscripcion')
            estado = request.POST.get('estado_evento')
            permitir_participantes = request.POST.get('permitir_participantes')

            # Aforo
            aforo = request.POST.get('cantidad_personas') if permitir_participantes == '1' else None

            # Archivos
            archivo_imagen = request.FILES.get('imagen_evento')
            archivo_programacion = request.FILES.get('documento_evento')

            # Obtener ID de administrador (puede estar vacío si no hay login aún)
            administrador_id = request.session.get('administrador_id')

            # Crear evento
            evento = Eventos.objects.create(
                eve_nombre=nombre,
                eve_descripcion=descripcion,
                eve_ciudad=ciudad,
                eve_lugar=lugar,
                eve_fecha_inicio=datetime.strptime(fecha_inicio, "%Y-%m-%d").date(),
                eve_fecha_fin=datetime.strptime(fecha_fin, "%Y-%m-%d").date(),
                eve_estado=estado,
                eve_imagen=archivo_imagen,
                eve_capacidad=int(aforo) if aforo else 0,
                eve_tienecosto=True if inscripcion == 'Si' else False,
                eve_programacion=archivo_programacion,
                eve_administrador_fk_id= 1 if administrador_id is None else administrador_id,
            )

            # Relación con categoría
            EventosCategorias.objects.create(
                eve_cat_evento_fk=evento,
                eve_cat_categoria_fk_id=categoria
            )

            messages.success(request, 'Evento creado exitosamente')
            return redirect('administrador:index_administrador')

        except Exception as e:
            print(f"Error al crear evento: {e}")
           

    # GET: mostrar formulario
    context = {
        'areas': obtener_areas_eventos(),
        'administrador': request.session.get('admin_nombre'),
    }
    return render(request, 'app_administrador/crearevento.html', context)

def inicio(request):
    # Obtener eventos (si tienes el modelo)
    eventos = Eventos.objects.all()
    
    # Por ahora con datos hardcodeados como en tu ejemplo
    context = {
        'administrador': request.session.get('admin_nombre'),
        'eventos': eventos,
    }
    
    return render(request, 'app_administrador/admin.html', context)

@require_http_methods(["GET"])
def obtener_evento(request, evento_id):
    try:
        evento = Eventos.objects.get(pk=evento_id)
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

    # Contar participantes y asistentes admitidos
    participantes = ParticipantesEventos.objects.filter(par_eve_participante_fk=evento_id, par_eve_estado='Admitido').count()
    asistentes = AsistentesEventos.objects.filter(asi_eve_asistente_fk=evento_id, asi_eve_estado='Admitido').count()


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
        'cantidad_participantes': participantes,
        'cantidad_asistentes': asistentes,
    }

    return JsonResponse(datos_evento)

@csrf_exempt 
def eliminar_evento(request, evento_id):
    
        try:
            evento = Eventos.objects.get(id=evento_id)
            evento.delete()
            return JsonResponse({'mensaje': 'Evento eliminado correctamente'})
        except Eventos.DoesNotExist:
            return JsonResponse({'mensaje': 'Evento no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'mensaje': f'Error al eliminar el evento: {str(e)}'}, status=500)

def inicio_sesion_administrador(request):
    if request.method == "POST":
        cedula = request.POST.get("cedula")

        try:
            admin = Administradores.objects.get(adm_cedula=cedula)
            # Guardar en la sesión
            request.session['admin_cedula'] = admin.id
            request.session['admin_nombre'] = admin.adm_nombre

            # Redirigir pasando el nombre como parámetro de URL
            return redirect('administrador:index_administrador')
        except Administradores.DoesNotExist:
            messages.error(request, "Cédula no válida")

    return render(request, 'app_administrador/inicio_sesion.html')