from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
import random
import qrcode
import string


import os
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.conf import settings

def generar_pdf(id_participante, usuario, id_evento, tipo="participante"):
    """
    Genera un PDF con QR y lo guarda en media/qr_participantes/ o media/qr_asistentes/.
    
    Parámetros:
    - id_participante: ID del participante o asistente
    - usuario: nombre o identificador para el PDF
    - id_evento: ID del evento
    - tipo: 'participante' o 'asistente'
    
    Retorna:
    - Ruta relativa al archivo para guardar en la base de datos
    """
    
    # 🟢 Crear el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    codigo = f"{id_participante}{id_evento}"
    qr.add_data(codigo)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    # 🖼️ Guardar QR en buffer
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_image = ImageReader(qr_buffer)

    # 📝 Crear PDF en memoria
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.drawString(200, 750, f"Entrada: {usuario}")
    c.drawImage(qr_image, 200, 600, 150, 150)
    c.save()
    pdf_buffer.seek(0)

    # 📁 Definir subcarpeta según tipo
    if tipo == "asistente":
        subcarpeta = "pdf/qr_asistentes"
    else:
        subcarpeta = "pdf/qr_participantes"

    carpeta_destino = os.path.join(settings.MEDIA_ROOT, subcarpeta)
    os.makedirs(carpeta_destino, exist_ok=True)

    # 📄 Nombre del archivo
    pdf_filename = f"{tipo}_{id_participante}_{id_evento}.pdf"
    pdf_path = os.path.join(carpeta_destino, pdf_filename)

    # 💾 Guardar en disco
    with open(pdf_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())

    # 🔁 Retornar ruta relativa para guardar en modelo o mostrar
    ruta_relativa = os.path.join(subcarpeta, pdf_filename)
    return ruta_relativa


def generar_clave_acceso(longitud=6):
    caracteres = string.ascii_letters + string.digits  # Letras (mayúsculas y minúsculas) + números
    clave = ''.join(random.choice(caracteres) for _ in range(longitud))
    return clave
