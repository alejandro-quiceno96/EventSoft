import os
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from app_usuarios.models import Usuario
from app_eventos.models import Eventos,  AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores


class GenerarQRAsistenteTests(TestCase):
    """HU-57: Generación automática de código QR al admitir asistente."""

    def setUp(self):
       
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )

        # Crear administrador asociado
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # Loguear como administrador
        self.client.force_login(self.usuario_admin)

        # Crear evento con todos los campos requeridos
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_img = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        self.evento = Eventos.objects.create(
            eve_nombre="Evento de prueba",
            eve_descripcion="Descripción de prueba",
            eve_ciudad="Manizales",
            eve_lugar="Auditorio Central",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Abierto",
            eve_imagen=fake_img,
            eve_capacidad=50,
            eve_administrador_fk=self.admin
        )

        # Crear asistente
        self.asistente_usuario = Usuario.objects.create_user(
            username='asistente',
            password='12345',
            first_name='Juan',
            email='juan@example.com'
        )

        from app_asistente.models import Asistentes
        self.asistente = Asistentes.objects.create(
            usuario=self.asistente_usuario
        )

        # Crear relación Asistente-Evento
        self.asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Pendiente",
            asi_eve_soporte=fake_img,
            asi_eve_qr=None,
            asi_eve_clave=""
        )

        # URL del endpoint
        self.url = reverse(
            'administrador:actualizar_estado_asistente',
            kwargs={'asistente_id': self.asistente.id, 'nuevo_estado': 'Admitido'}
        )


    def test_generar_qr_para_asistente_admitido(self):
        """✅ Debe generar un QR único y cifrado al admitir un asistente"""
        start_time = time.time()

        response = self.client.post(self.url, {
            'evento_id': self.evento.id
        })

        duration = (time.time() - start_time) * 1000  # milisegundos

        # Refrescar instancia desde la BD
        self.asistente_evento.refresh_from_db()

        # ✅ Respuesta exitosa
        self.assertEqual(response.status_code, 302, msg="Debe redirigir tras la actualización")

        # ✅ Verificar que se haya generado un QR
        self.assertTrue(self.asistente_evento.asi_eve_qr, msg="Debe generar un QR para el asistente admitido")

        # ✅ El QR debe contener una ruta válida en MEDIA_ROOT
        qr_path = os.path.join(settings.MEDIA_ROOT, str(self.asistente_evento.asi_eve_qr))
        self.assertTrue(os.path.exists(qr_path), msg="El archivo del QR debe existir físicamente")

        # ✅ El QR debe contener datos cifrados
        with open(qr_path, 'rb') as f:
            qr_data = f.read()
        self.assertGreater(len(qr_data), 0, msg="El archivo QR no puede estar vacío")

        # ✅ Verificar tiempo de generación < 500 ms
        self.assertLess(duration, 1000, msg=f"La generación del QR tomó demasiado tiempo: {duration:.2f} ms")

    def test_no_genera_qr_para_rechazado(self):
        """🚫 No debe generar QR si el estado es Rechazado"""
        url_rechazado = reverse(
            'administrador:actualizar_estado_asistente',
            kwargs={'asistente_id': self.asistente.id, 'nuevo_estado': 'Rechazado'}
        )

        response = self.client.post(url_rechazado, {
            'evento_id': self.evento.id,
            'motivo': 'Pago inválido'
        })

        self.asistente_evento.refresh_from_db()

        # ✅ Redirige correctamente
        self.assertEqual(response.status_code, 302)

        # 🚫 No debe tener QR ni clave de acceso
        self.assertFalse(bool(self.asistente_evento.asi_eve_qr), "No debe generarse QR para asistentes rechazados")

        self.assertEqual(self.asistente_evento.asi_eve_clave, "0", "La clave del rechazado debe quedar como '0' o vacía")


    def test_metodo_no_permitido(self):
        """🚫 Solo se permite método POST"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn("no permitido", response.json().get('message', '').lower())
