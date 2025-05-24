# app_asistente/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
import io
import base64
from datetime import datetime

from .models import Evento, Asistentes, AsistenteEvento, Categoria, EventoCategoria


def preinscribir_asistente(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    return render(request, 'app_asistente/asistente/asistente.html', {'evento': evento.id, 'cobro': evento.tiene_costo})

def home(request):
    
    return render(request, 'app_asistente/home.html')


def registrar_asistente(request):
    if request.method == 'POST':
        asi_id = request.POST['asi_id']
        asi_nombre = request.POST['asi_nombre']
        asi_correo = request.POST['asi_correo']
        asi_telefono = request.POST['asi_telefono']
        eve_id = request.POST['eve_id']
        fecha_hora = datetime.now()

        comprobante_pago = request.FILES.get('comprobante_pago')
        comprobante_data = comprobante_pago.read() if comprobante_pago else None

        estado_asistente = 'Pendiente' if comprobante_data else 'Admitido'

        asistente, created = Asistentes.objects.get_or_create(
            asi_cedula=asi_id,
            defaults={
                'asi_nombre': asi_nombre,
                'asi_correo': asi_correo,
                'asi_telefono': asi_telefono
            }
        )

        asistente_evento = AsistenteEvento.objects.create(
            asistente=asistente,
            evento_id=eve_id,
            fecha_hora=fecha_hora,
            estado=estado_asistente,
            soporte=comprobante_data,
            qr=None if estado_asistente == 'Pendiente' else generar_pdf(asi_id, 'Asistente', eve_id),
            clave=None if estado_asistente == 'Pendiente' else generar_clave_acceso()
        )

        messages.success(request, "Asistente registrado con éxito")
        return redirect('/')
    else:
        return render(request, 'app_asistente/asistente.html')



def qr_asistentesz_ver(request, evento_id):
    participante_id = request.GET.get('participante_id')
    asistente_evento = AsistenteEvento.objects.filter(
        evento_id=evento_id,
        asistente__asi_cedula=participante_id
    ).first()
    if asistente_evento and asistente_evento.qr:
        return FileResponse(io.BytesIO(asistente_evento.qr), content_type='application/pdf')
    else:
        return HttpResponse("Documento no encontrado", status=404)

def descargar_qr_asistente(request, evento_id):
    participante_id = request.GET.get('participante_id')
    asistente_evento = AsistenteEvento.objects.filter(
        evento_id=evento_id,
        asistente__asi_cedula=participante_id
    ).first()
    if asistente_evento and asistente_evento.qr:
        filename = f"qr_evento_{evento_id}_asistente_{participante_id}.pdf"
        response = FileResponse(io.BytesIO(asistente_evento.qr), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse("Documento no encontrado", status=404)

def evento_asistentes(request, evento_id, asistente_id):
    evento = Evento.objects.filter(id=evento_id).first()
    clave_acceso = AsistenteEvento.objects.filter(evento_id=evento_id, asistente__asi_cedula=asistente_id).first()
    if not evento:
        return JsonResponse({"error": "Evento no encontrado"}, status=404)

    datos_evento = {
        'eve_id': evento.id,
        'eve_nombre': evento.nombre,
        'eve_descripcion': evento.descripcion,
        'eve_ciudad': evento.ciudad,
        'eve_lugar': evento.lugar,
        'eve_fecha_inicio': evento.fecha_inicio,
        'eve_fecha_fin': evento.fecha_fin,
        'eve_estado': evento.estado,
        'eve_imagen': base64.b64encode(evento.imagen).decode('utf-8') if evento.imagen else None,
        'eve_cantidad': evento.capacidad if evento.capacidad is not None else 'Cupos ilimitados',
        'eve_costo': evento.tiene_costo,
        'eve_programacion': base64.b64encode(evento.programacion).decode('utf-8') if evento.programacion else None,
        'eve_clave_acceso': clave_acceso.clave if clave_acceso else None,
    }

    categoria = (
        Categoria.objects
        .filter(eventocategoria__evento_id=evento_id)
        .values_list('nombre', flat=True)
        .first()
    )
    datos_evento['eve_categoria'] = categoria if categoria else None

    return JsonResponse(datos_evento)

@require_http_methods(["POST"])
def eventos_pre_asistente(request):
    cedula = request.POST['cedula']
    eventos = (
        Evento.objects
        .filter(asistenteevento__asistente__asi_cedula=cedula)
        .annotate(estado=F('asistenteevento__estado'))
    )
    eventos_lista = []
    for evento in eventos:
        evento_dict = {
            "id": evento.id,
            "nombre": evento.nombre,
            "descripcion": evento.descripcion,
            "ciudad": evento.ciudad,
            "lugar": evento.lugar,
            "fecha_inicio": evento.fecha_inicio,
            "fecha_fin": evento.fecha_fin,
            "estado": evento.estado
        }
        eventos_lista.append(evento_dict)
    return render(request, 'app_asistente/eventos_asistentes.html', {'eventos': eventos_lista, 'cedula_participante': cedula})

def descargar_programacion(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if evento.programacion:
        filename = f"programacion_evento_{evento_id}.pdf"
        response = FileResponse(io.BytesIO(evento.programacion), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse("Documento no encontrado", status=404)

@require_http_methods(["POST"])
def cancelar_inscripcion_asistente(request, evento_id):
    participante_id = request.POST.get('participante_id')
    if not participante_id:
        return JsonResponse({"success": False, "error": "ID del asistente faltante"}, status=400)
    try:
        asistente_evento = AsistenteEvento.objects.filter(
            evento_id=evento_id,
            asistente__asi_cedula=participante_id
        ).first()
        if asistente_evento:
            asistente_evento.delete()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "No se encontró la inscripción"}, status=404)
    except Exception as e:
        print("Error:", e)
        return JsonResponse({"success": False, "error": "Error al procesar la solicitud"}, status=500)
