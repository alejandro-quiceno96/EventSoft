# eventos/supabase_client.py
from supabase import create_client
from django.conf import settings
import os
import unicodedata
import re
import time

# Cargar datos desde variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "media")  # "media" como valor por defecto

# Crear cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_imagen_supabase(file, carpeta):
    if not file:
        return None
        
    if getattr(file, 'name', None):
        original_name, ext = os.path.splitext(file.name)
        file_data = file.read()
        content_type = getattr(file, 'content_type', 'application/octet-stream')
    elif isinstance(file, str):
        # Es una ruta al archivo local (posiblemente un reporte QR o PDF autogenerado)
        ruta_absoluta = os.path.join(settings.MEDIA_ROOT, file) if not os.path.isabs(file) else file
        if not os.path.exists(ruta_absoluta):
            return None
        original_name, ext = os.path.splitext(os.path.basename(ruta_absoluta))
        with open(ruta_absoluta, 'rb') as f:
            file_data = f.read()
        content_type = 'application/pdf' if ext.lower() == '.pdf' else 'application/octet-stream'
    else:
        return None
    
    # Normalizar para quitar tildes (acentos)
    name = unicodedata.normalize('NFKD', original_name).encode('ascii', 'ignore').decode('ascii')
    # Dejar solo alfanuméricos y reemplazar los espacios por guiones bajos
    name = re.sub(r'[^\w\s-]', '', name).strip().lower()
    name = re.sub(r'[-\s]+', '_', name)
    
    # Concatenar con timestamp para evitar colisiones
    nombre = f"{name}_{int(time.time())}{ext}"

    # Subir archivo al bucket
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        f"{carpeta}/{nombre}",
        file_data,
        {"content-type": content_type}
    )

    # Obtener URL pública
    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(f"{carpeta}/{nombre}")
    
    # Si devuelve dict extrae la url
    if isinstance(public_url, dict) and 'public_url' in public_url:
        public_url = public_url['public_url']
        
    return public_url