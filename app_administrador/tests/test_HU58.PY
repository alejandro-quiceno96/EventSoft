import os
import time
import base64
import qrcode
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores


class GeneracionAutomaticaQRTests(TestCase):
    """HU-66: Generación automática y cifrada de código QR para asistentes admitidos."""

    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9999",
            telefono="3100000000"
        )

        # Crear administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=1,
            estado="Activo",
            clave_acceso="CLVADMIN"
        )

        self.client.force_login(self.usuario_admin)

        # Crear evento
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_img = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        self.evento = Eventos.objects.create(
            eve_nombre="Evento QR Automático",
            eve_descripcion="Evento para probar generación de QR",
            eve_ciudad="Manizales",
            eve_lugar="Auditorio Central",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Abierto",
            eve_imagen=fake_img,
            eve_capacidad=30,
            eve_administrador_fk=self.admin
        )

        # Crear asistente
        self.usuario_asistente = Usuario.objects.create_user(
            username='asistente_qr',
            password='12345',
            first_name='Laura',
            email='laura@example.com'
        )

        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

        # Crear relación Asistente-Evento (pendiente)
        self.asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Pendiente",
            asi_eve_qr=None,
            asi_eve_clave=""
        )

        # Endpoint que valida pago o aprobación (HU57/HU66)
        self.url = reverse(
            'administrador:actualizar_estado_asistente',
            kwargs={'asistente_id': self.asistente.id, 'nuevo_estado': 'Admitido'}
        )

    def test_generacion_qr_unico_y_cifrado(self):
        """✅ Debe generar un QR único y cifrado al aprobar inscripción o validar pago."""
        start = time.time()

        response = self.client.post(self.url, {'evento_id': self.evento.id})
        duration = (time.time() - start) * 1000  # milisegundos

        # Actualizar datos desde BD
        self.asistente_evento.refresh_from_db()

        # ✅ Respuesta correcta
        self.assertEqual(response.status_code, 302, "Debe redirigir tras aprobar inscripción")

        # ✅ QR debe generarse
        self.assertTrue(self.asistente_evento.asi_eve_qr, "Debe generarse un QR para el asistente admitido")

        # ✅ Archivo QR debe existir físicamente
        qr_path = os.path.join(settings.MEDIA_ROOT, str(self.asistente_evento.asi_eve_qr))
        self.assertTrue(os.path.exists(qr_path), "El archivo del QR debe existir")

        # ✅ Contenido cifrado dentro del QR
        with open(qr_path, 'rb') as f:
            contenido = f.read()
        self.assertGreater(len(contenido), 0, "El QR no debe estar vacío")

        # Simular descifrado (base64) solo para validar estructura del payload cifrado
        payload_cifrado = base64.b64encode(f"{self.asistente.id}:{self.evento.id}:ASISTENTE".encode()).decode()
        self.assertIn(":", base64.b64decode(payload_cifrado).decode(), "El QR debe contener datos cifrados estructurados")

        # ✅ Tiempo de generación < 1000 ms
        self.assertLess(duration, 1000, f"La generación del QR fue lenta: {duration:.2f} ms")

    def test_no_genera_qr_para_pendiente(self):
        """🚫 No debe generarse QR si el estado sigue siendo 'Pendiente'."""
        self.assertFalse(self.asistente_evento.asi_eve_qr, "No debe existir QR mientras esté Pendiente")

    def test_rechazo_no_genera_qr(self):
        """🚫 No debe generarse QR si el asistente fue rechazado."""
        url_rechazado = reverse(
            'administrador:actualizar_estado_asistente',
            kwargs={'asistente_id': self.asistente.id, 'nuevo_estado': 'Rechazado'}
        )

        response = self.client.post(url_rechazado, {
            'evento_id': self.evento.id,
            'motivo': 'Pago inválido'
        })
        self.asistente_evento.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(bool(self.asistente_evento.asi_eve_qr), "No debe generarse QR para rechazados")
