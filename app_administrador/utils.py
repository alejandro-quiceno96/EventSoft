import random
import string
import os
import io
import qrcode
import base64
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
from django.db.models  import Avg

from app_evaluador.models import Calificaciones
from app_participante.models import Participantes
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores
from app_criterios.models import Criterios
from app_eventos.models import Eventos, EvaluadoresEventos, ParticipantesEventos, AsistentesEventos, Proyecto
from django.shortcuts import get_object_or_404
from app_certificados.models import Certificado
from django.http import HttpResponse
from datetime import datetime
import locale


def generar_pdf(id_participante, usuario, id_evento, tipo="expositor"):
    qr_data = f"{id_participante}{id_evento}"
    qr_img = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    if tipo == "evaluador":
        evaluador = Evaluadores.objects.get(id=id_participante)
        usuario = evaluador.usuario.first_name + " " + evaluador.usuario.last_name
        id_participante = evaluador.usuario.documento_identidad
    elif tipo == "asistente":
        asistente = Asistentes.objects.get(id=id_participante)
        usuario = asistente.usuario.first_name + " " + asistente.usuario.last_name
        id_participante = asistente.usuario.documento_identidad
    else:
        participante = Participantes.objects.get(id=id_participante)
        usuario = participante.usuario.first_name + " " + participante.usuario.last_name
        id_participante = participante.usuario.documento_identidad
        
    html_string = render_to_string("app_administrador/entrada_pdf.html", {
        "usuario": usuario,
        "id_participante": id_participante,
        "id_evento": id_evento,
        "qr_base64": qr_base64,
    })

    if tipo == "asistente":
        subcarpeta = "pdf/qr_asistentes"
    elif tipo == "expositor":
        subcarpeta = "pdf/qr_participantes"
    else:
        subcarpeta = "pdf/qr_evaluador"

    carpeta_destino = os.path.join(settings.MEDIA_ROOT, subcarpeta)
    os.makedirs(carpeta_destino, exist_ok=True)

    pdf_filename = f"{tipo}_{id_participante}_{id_evento}.pdf"
    pdf_path = os.path.join(carpeta_destino, pdf_filename)

    css_path = os.path.join(
    settings.BASE_DIR, "app_administrador", "static", "app_administrador", "css", "entrada_pdf.css"
)
    HTML(string=html_string).write_pdf(pdf_path, stylesheets=[CSS(filename=css_path)])

    return os.path.join(subcarpeta, pdf_filename)

def generar_clave_acceso(longitud=6):
    caracteres = string.ascii_letters + string.digits  # Letras (mayúsculas y minúsculas) + números
    clave = ''.join(random.choice(caracteres) for _ in range(longitud))
    return clave


def obtener_ranking(evento_id):
    """
    Retorna el ranking de proyectos con sus expositores, puntaje final y medallas para el top 3.
    """

    # Subconsulta: promedio por criterio y proyecto
    subquery = (
        Calificaciones.objects
        .values('clas_proyecto_fk', 'cal_criterio_fk')
        .annotate(promedio_criterio=Avg('cal_valor'))
    )

    # Diccionario temporal para almacenar acumulados de puntajes ponderados
    ranking_dict = {}

    for row in subquery:
        criterio = Criterios.objects.filter(
            id=row['cal_criterio_fk'],
            cri_evento_fk=evento_id
        ).first()

        if criterio:
            proyecto_id = row['clas_proyecto_fk']
            ponderado = row['promedio_criterio'] * criterio.cri_peso / 100

            if proyecto_id not in ranking_dict:
                ranking_dict[proyecto_id] = 0
            ranking_dict[proyecto_id] += ponderado

    # Ordenar por puntaje final descendente
    ranking_ordenado = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    # Construir lista final para usar en PDF o template
    ranking = []
    for index, (proyecto_id, puntaje) in enumerate(ranking_ordenado, start=1):
        proyecto = Proyecto.objects.get(id=proyecto_id)

        # Obtener expositores vinculados al proyecto en este evento
        expositores = ParticipantesEventos.objects.filter(
            par_eve_proyecto=proyecto,
            par_eve_evento_fk=evento_id
        )

        lista_expositores = [
            f"{e.par_eve_participante_fk.usuario.first_name} {e.par_eve_participante_fk.usuario.last_name}"
            for e in expositores
        ]

        # Asignar medalla solo al top 3
        medalla = None
        if index == 1:
            medalla = "🥇 Oro"
        elif index == 2:
            medalla = "🥈 Plata"
        elif index == 3:
            medalla = "🥉 Bronce"

        ranking.append({
            'posicion': index,
            'id': proyecto.id,
            'proyecto': proyecto.pro_nombre,
            'expositores': lista_expositores,
            'puntaje_final': round(puntaje, 2),
            'medalla': medalla
        })

    return ranking


def generar_certificados(request, evento_id, tipo, usuario):
    evento = get_object_or_404(Eventos, id=evento_id)
    certificado = get_object_or_404(Certificado, evento_fk=evento)
    print(certificado.diseño.url)
 
    # Obtener instancia del participante
    if tipo == 'participante':
        participante = get_object_or_404(Participantes, id=usuario)
    elif tipo == 'evaluador':  
        participante = get_object_or_404(Evaluadores, id=usuario)
    elif tipo == 'asistente':
        participante = get_object_or_404(Asistentes, id=usuario)
    else:
        return HttpResponse("Tipo de participante no válido", status=400)

    # Configurar fecha en español
    try:
        locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    fecha_formateada = datetime.now().strftime('%d de %B de %Y')
    fecha_inicio = evento.eve_fecha_inicio.strftime('%d de %B de %Y')

    # Renderizar plantilla HTML con datos del certificado
    html_string = render_to_string('app_administrador/pdf_certificado.html', {
        'certificado': certificado,
        'evento': evento,
        'now': fecha_formateada,
        'rol_participante': tipo.capitalize(),
        'nombre_participante': " ".join(filter(None, [
            participante.usuario.first_name.upper(),
            participante.usuario.segundo_nombre.upper() ,
            participante.usuario.last_name.upper(),
            participante.usuario.segundo_apellido.upper()
        ])),
        'documento_participante': participante.usuario.documento_identidad,
        'fecha_inicio': fecha_inicio,
    })

    # Generar PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    return pdf_file

def generar_reconocmiento(request, evento_id, usuario):
    evento = get_object_or_404(Eventos, id=evento_id)
    certificado = get_object_or_404(Certificado, evento_fk=evento)
    
    participante = get_object_or_404(Participantes, id=usuario)
    # Configurar fecha en español
    try:
        locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    fecha_formateada = datetime.now().strftime('%d de %B de %Y')
    fecha_inicio = evento.eve_fecha_inicio.strftime('%d de %B de %Y')

    # Renderizar plantilla HTML con datos del certificado
    html_string = render_to_string('app_administrador/pdf_certificado_primer_lugar.html', {
        'certificado': certificado,
        'evento': evento,
        'now': fecha_formateada,
        'nombre_participante': " ".join(filter(None, [
            participante.usuario.first_name.upper(),
            participante.usuario.segundo_nombre.upper() ,
            participante.usuario.last_name.upper(),
            participante.usuario.segundo_apellido.upper()
        ])),
        'documento_participante': participante.usuario.documento_identidad,
        'fecha_inicio': fecha_inicio,
    })

    # Generar PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    return pdf_file
