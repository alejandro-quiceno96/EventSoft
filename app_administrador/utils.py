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


def generar_pdf(id_participante, usuario, id_evento, tipo="participante"):
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
    elif tipo == "participante":
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

    # Subconsulta: promedio por criterio y participante
    subquery = (
        Calificaciones.objects
        .values('clas_participante_fk', 'cal_criterio_fk')
        .annotate(promedio_criterio=Avg('cal_valor'))
    )

    # Diccionario temporal para almacenar acumulados
    ranking_dict = {}

    for row in subquery:
        criterio = Criterios.objects.filter(id=row['cal_criterio_fk'], cri_evento_fk=evento_id).first()
        if criterio:
            participante_id = row['clas_participante_fk']
            ponderado = row['promedio_criterio'] * criterio.cri_peso / 100

            if participante_id not in ranking_dict:
                ranking_dict[participante_id] = 0
            ranking_dict[participante_id] += ponderado

    # Ordenar por promedio ponderado descendente
    ranking_ordenado = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)

    # Construir lista para el template
    ranking = []
    for participante_id, promedio in ranking_ordenado:
        participante = Participantes.objects.get(id=participante_id)
        ranking.append({
            'id': participante.usuario.id,
            'nombre': participante.usuario.first_name + " " + participante.usuario.last_name,
            'promedio': round(promedio, 2)
        })

    return ranking