from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from app_asistente.models import Asistentes
from app_eventos.models import AsistentesEventos, Eventos
from django.conf import settings
from django.utils import timezone
from app_administrador.models import Administradores
from app_usuarios.models import Usuario

User = get_user_model()

class ActualizarEstadoAsistenteTests(TestCase):

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


        # Crear usuario asistente
        self.usuario_asistente = User.objects.create_user(
            username="asistente",
            password="pass123",
            email="asistente@test.com"
        )
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

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

        # Relación AsistenteEvento
        self.asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Pendiente"
        )

        self.url_admitir = reverse(
            "administrador:actualizar_estado_asistente",
            kwargs={"asistente_id": self.asistente.id, "nuevo_estado": "Admitido"}
        )

        self.url_rechazar = reverse(
            "administrador:actualizar_estado_asistente",
            kwargs={"asistente_id": self.asistente.id, "nuevo_estado": "Rechazado"}
        )

    @patch("app_administrador.views.generar_pdf", return_value="qr_test.pdf")
    @patch("app_administrador.views.generar_clave_acceso", return_value="ABC123")
    @patch("app_administrador.views.EmailMultiAlternatives.send", return_value=True)
    def test_actualizar_estado_admitido(self, mock_send, mock_clave, mock_pdf):
        """Debe actualizar el estado a 'Admitido' y generar QR y clave"""
        response = self.client.post(self.url_admitir, {"evento_id": self.evento.id})
        self.asistente_evento.refresh_from_db()

        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertEqual(self.asistente_evento.asi_eve_estado, "Admitido")
        self.assertEqual(self.asistente_evento.asi_eve_clave, "ABC123")
        self.assertEqual(self.asistente_evento.asi_eve_qr, "qr_test.pdf")
        mock_send.assert_called_once()

    @patch("app_administrador.views.EmailMultiAlternatives.send", return_value=True)
    def test_actualizar_estado_rechazado(self, mock_send):
        """Debe actualizar el estado a 'Rechazado' y guardar motivo"""
        response = self.client.post(
            self.url_rechazar,
            {"evento_id": self.evento.id, "motivo": "No cumple requisitos"}
        )
        self.asistente_evento.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.asistente_evento.asi_eve_estado, "Rechazado")
        self.assertFalse(self.asistente_evento.asi_eve_qr.name)


        self.assertEqual(str(self.asistente_evento.asi_eve_clave), "0")

        mock_send.assert_called_once()

    def test_post_sin_evento_id(self):
        """Debe devolver error 400 si no se envía evento_id"""
        response = self.client.post(self.url_rechazar, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("ID de evento no proporcionado", response.json()["message"])

    def test_asistente_no_en_evento(self):
        """Debe devolver error 404 si el asistente no pertenece al evento"""
        self.asistente_evento.delete()
        response = self.client.post(self.url_rechazar, {"evento_id": self.evento.id})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Asistente no encontrado", response.json()["message"])

    def test_metodo_get_no_permitido(self):
        """Debe devolver error 405 si se usa GET"""
        response = self.client.get(self.url_admitir)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Método no permitido", response.json()["message"])
