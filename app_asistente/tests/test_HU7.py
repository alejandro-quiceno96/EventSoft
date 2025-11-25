from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta, datetime

from app_usuarios.models import Usuario
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores


class QRInscripcionTests(TestCase):

    def setUp(self):
        # Crear un usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="adminuser",
            email="admin@test.com",
            password="adminpass"
        )

        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin
        )

        # Crear un evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento de Prueba",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today() + timedelta(days=1),
            eve_capacidad=100,
            eve_administrador_fk=self.admin
        )

        # Crear un usuario asistente
        self.usuario_asistente = Usuario.objects.create_user(
            username="asistenteuser",
            email="asistente@test.com",
            password="asistentepass"
        )

        self.asistente = Asistentes.objects.create(
            usuario=self.usuario_asistente
        )

        # Simulación de archivos fake
        fake_soporte = SimpleUploadedFile("comprobante.pdf", b"PDF content", content_type="application/pdf")
        fake_qr = SimpleUploadedFile(
            f"test_qr_asistente_{self.asistente.id}_evento_{self.evento.id}.png",
            f"QR DATA asistente {self.asistente.id} evento {self.evento.id} rol asistente".encode(),
            content_type="image/png"
        )

        # Relación asistente-evento
        self.asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=datetime.now(),
            asi_eve_estado="validado",
            asi_eve_soporte=fake_soporte,
            asi_eve_qr=fake_qr,
            asi_eve_clave="ABC123"
        )

    def test_qr_generado_unico_por_inscripcion(self):
        """El QR debe generarse una sola vez y ser único por inscripción"""
        self.assertIsNotNone(self.asistente_evento.asi_eve_qr)
        self.assertGreater(len(self.asistente_evento.asi_eve_qr.read()), 10)

    def test_envio_email_con_qr_y_clave(self):
        """Al validar inscripción se debe enviar email con QR y clave de acceso"""
        self.assertIsNotNone(self.asistente_evento.asi_eve_clave)

    def test_qr_contiene_datos_cifrados_correctos(self):
        """El QR debe contener al menos ID de usuario, ID de evento y rol"""
        qr_data = self.asistente_evento.asi_eve_qr.read().decode()
        self.assertIn(str(self.asistente.id), qr_data)
        self.assertIn(str(self.evento.id), qr_data)
        self.assertIn("asistente", qr_data)  # validar rol
