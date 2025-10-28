from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from unittest.mock import patch
from django.utils import timezone
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_eventos.models import Eventos, ParticipantesEventos, Proyecto
from app_participante.models import Participantes
import datetime

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificacionAdmisionRechazoTest(TestCase):
    """HU17 - Pruebas automáticas para notificación de admisión o rechazo de proyectos"""

    def setUp(self):
        self.client = Client()

        # 🔹 Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=3,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # 🔹 Crear participante y usuario asociado
        self.usuario_participante = Usuario.objects.create_user(
            username="participante_test",
            email="participante@test.com",
            password="test12345",
            tipo_documento="CC",
            documento_identidad="2222",
            telefono="3010000000"
        )
        self.participante = Participantes.objects.create(usuario=self.usuario_participante)

        # 🔹 Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Evento de Prueba',
            eve_descripcion='Descripción del evento',
            eve_ciudad='Caldas',
            eve_lugar='Manizales',
            eve_fecha_inicio=datetime.date(2025, 10, 1),
            eve_fecha_fin=datetime.date(2025, 10, 3),
            eve_estado='Activo',
            eve_imagen='imagen/test.jpg',
            eve_capacidad=100,
            eve_administrador_fk=self.admin
        )

        # 🔹 Crear proyecto
        archivo = SimpleUploadedFile("documento.pdf", b"contenido de prueba", content_type="application/pdf")
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="COD12345",
            pro_nombre="Proyecto de Prueba",
            pro_descripcion="Descripción breve",
            pro_documentos=archivo,
            pro_estado="Pendiente"
        )

        # 🔹 Crear inscripción del participante al proyecto
        self.inscripcion = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=archivo,
            par_eve_estado="Pendiente",
            par_eve_qr="",
            par_eve_clave="",
            par_eve_proyecto=self.proyecto
        )

        # 🔹 URL del endpoint
        self.url = reverse('administrador:actualizar_estado', args=[self.proyecto.id, 'Admitido'])

    @patch("app_administrador.utils.generar_pdf", return_value="qr/test_qr.pdf")
    @patch("app_administrador.utils.generar_clave_acceso", return_value="CLAVE123")
    def test_envio_email_admision(self, mock_qr, mock_clave):
        """✅ Debe enviar correo de admisión correctamente"""
        self.client.login(username="admin_test", password="admin123")

        data = {'evento_id': self.evento.id}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertIn('estado=Admitido', response.url)

        # Validar actualización del estado
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.pro_estado, "Admitido")

        # Validar envío de correo
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertIn("Confirmación de inscripción", correo.subject)
        self.assertIn(self.evento.eve_nombre, correo.body or correo.alternatives[0][0])
        self.assertIn(self.participante.usuario.email, correo.to)

    @patch("app_administrador.utils.generar_pdf", return_value="qr/test_qr.pdf")
    @patch("app_administrador.utils.generar_clave_acceso", return_value="CLAVE123")
    def test_envio_email_rechazo_con_razon(self, mock_qr, mock_clave):
        """✅ Debe enviar correo de rechazo con razón especificada"""
        self.client.login(username="admin_test", password="admin123")

        url = reverse('administrador:actualizar_estado', args=[self.proyecto.id, 'Rechazado'])
        data = {'evento_id': self.evento.id, 'razon': 'Documento ilegible'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.pro_estado, "Rechazado")

        # Validar correo
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertIn("Notificación de rechazo", correo.subject)
        self.assertIn("Documento ilegible", correo.body or correo.alternatives[0][0])

    @patch("app_administrador.utils.generar_pdf", return_value="qr/test_qr.pdf")
    @patch("app_administrador.utils.generar_clave_acceso", return_value="CLAVE123")
    def test_envio_email_rechazo_sin_razon(self, mock_qr, mock_clave):
        """✅ Si no se proporciona razón, usa la razón por defecto"""
        self.client.login(username="admin_test", password="admin123")

        url = reverse('administrador:actualizar_estado', args=[self.proyecto.id, 'Rechazado'])
        data = {'evento_id': self.evento.id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.pro_estado, "Rechazado")

        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertIn("No se especificó el motivo del rechazo", correo.body or correo.alternatives[0][0])

    def test_proyecto_no_encontrado(self):
        """❌ Debe devolver 404 si el proyecto no existe"""
        self.client.login(username="admin_test", password="admin123")
        url = reverse('administrador:actualizar_estado', args=[999, 'Admitido'])
        data = {'evento_id': self.evento.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)

    def test_metodo_no_permitido(self):
        """❌ Debe devolver 405 si se accede con GET"""
        self.client.login(username="admin_test", password="admin123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertIn("Método no permitido", response_data.get("message", ""))

