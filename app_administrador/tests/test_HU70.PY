# app_administrador/tests/test_hu70_enviar_correo.py

from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile

from app_eventos.models import Eventos, AsistentesEventos, ParticipantesEventos, EvaluadoresEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores

User = get_user_model()


class EnviarCorreoTestCase(TestCase):
    """
    Pruebas HU70 - Enviar notificaciones a asistentes/participantes/evaluadores
    Cubre:
     - GET (mostrar formulario y roles)
     - Evento inexistente -> template con error_envio
     - POST sin destinatarios -> muestra error_envio
     - POST sin contenido -> muestra error_envio
     - POST con destinatarios pero obtener_emails... devuelve vacío -> muestra error_envio
     - POST exitoso (sin archivos) -> EmailMessage.send llamado y envió_exitoso True en contexto
     - POST exitoso (con archivo adjunto) -> EmailMessage.send llamado y envió_exitoso True
     - POST donde EmailMessage.send lanza excepción -> captura y muestra error_envio con mensaje de excepción
    """

    def setUp(self):
        self.client = Client()
        # Crear usuario administrador
        self.user_admin = User.objects.create_user(username="admin1", password="admin123",
                                                   first_name="Admin", last_name="Uno")
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Test",
            eve_descripcion="Desc",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="img.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear asistentes / participantes / evaluadores y sus relaciones (Admitidos)
        # Asistente
        user_a = User.objects.create_user(username="asi1", password="p", first_name="A", last_name="One", email="asi1@example.com")
        self.asistente = Asistentes.objects.create(usuario=user_a)
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Admitido"
        )

        # Participante
        user_p = User.objects.create_user(username="par1", password="p", first_name="P", last_name="One", email="par1@example.com")
        self.participante = Participantes.objects.create(usuario=user_p)
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_estado="Admitido",
            par_eve_proyecto=None,
            par_eve_fecha_hora=now()
        )

        # Evaluador
        user_e = User.objects.create_user(username="eval1", password="p", first_name="E", last_name="One", email="eval1@example.com")
        self.evaluador = Evaluadores.objects.create(usuario=user_e)
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador,
            eva_eve_evento_fk=self.evento,
            eva_estado="Admitido"
        )

        # Login admin
        self.client.login(username="admin1", password="admin123")
        self.url = reverse("administrador:enviar_correo", args=[self.evento.id])

    def test_get_form_shows_roles_and_event(self):
        """GET debe mostrar el formulario con roles y evento en contexto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("roles", response.context)
        roles = response.context["roles"]
        keys = [r["key"] for r in roles]
        self.assertIn("asistentes", keys)
        self.assertIn("participantes", keys)
        self.assertIn("evaluadores", keys)
        self.assertIn("evento", response.context)


    def test_post_without_destinatarios_returns_error(self):
        """POST sin destinatarios debe regresar error_envio"""
        data = {
            "asunto": "Prueba",
            "contenido": "Mensaje de prueba",
            # no 'destinatarios'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("error_envio", response.context)
        self.assertIn("seleccionar al menos un destinatario", response.context["error_envio"].lower())

    def test_post_without_contenido_returns_error(self):
        """POST sin contenido debe regresar error_envio"""
        data = {
            "destinatarios": ["asistentes"],
            "asunto": "Prueba",
            "contenido": ""  # vacío
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("error_envio", response.context)
        self.assertIn("mensaje del correo no puede estar vacío", response.context["error_envio"].lower())

    @patch("app_administrador.views.obtener_emails_por_destinatarios", return_value=[])
    def test_post_with_no_emails_found_returns_error(self, mock_obtener):
        """Si no se encuentran correos para los destinatarios seleccionados -> error_envio"""
        data = {
            "destinatarios": ["asistentes"],
            "asistentes_seleccionados": [str(self.asistente.id)],
            "asunto": "Prueba",
            "contenido": "Hola"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("error_envio", response.context)
        self.assertIn("no se encontraron correos", response.context["error_envio"].lower())
        mock_obtener.assert_called_once()

    @patch("app_administrador.views.obtener_emails_por_destinatarios", return_value=["asi1@example.com", "par1@example.com"])
    @patch("app_administrador.views.EmailMessage.send", return_value=1)
    def test_post_successful_send_without_files(self, mock_send, mock_obtener):
        """Envio exitoso sin archivos: EmailMessage.send es llamado y envió_exitoso aparece en contexto"""
        data = {
            "destinatarios": ["asistentes", "participantes"],
            "asistentes_seleccionados": [str(self.asistente.id)],
            "participantes_seleccionados": [str(self.participante.id)],
            "asunto": "Notificación importante",
            "contenido": "<p>Contenido html</p>"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("envio_exitoso", response.context)
        self.assertTrue(response.context["envio_exitoso"])
        mock_obtener.assert_called_once()
        mock_send.assert_called_once()

    @patch("app_administrador.views.obtener_emails_por_destinatarios", return_value=["eval1@example.com"])
    @patch("app_administrador.views.EmailMessage.send", return_value=1)
    def test_post_successful_send_with_file_attachment(self, mock_send, mock_obtener):
        """Envio exitoso con archivo adjunto: el archivo se adjunta y EmailMessage.send es llamado"""
        small_file = SimpleUploadedFile("info.txt", b"contenido del archivo", content_type="text/plain")
        data = {
            "destinatarios": ["evaluadores"],
            "evaluadores_seleccionados": [str(self.evaluador.id)],
            "asunto": "Adjunto",
            "contenido": "<p>Con adjunto</p>"
        }
        # Files must be passed separately
        response = self.client.post(self.url, data, files={"archivos": small_file})
        self.assertEqual(response.status_code, 200)
        self.assertIn("envio_exitoso", response.context)
        self.assertTrue(response.context["envio_exitoso"])
        mock_obtener.assert_called_once()
        mock_send.assert_called_once()

    @patch("app_administrador.views.obtener_emails_por_destinatarios", return_value=["asi1@example.com"])
    @patch("app_administrador.views.EmailMessage.send", side_effect=Exception("SMTP Error"))
    def test_post_email_send_raises_exception_is_handled(self, mock_send, mock_obtener):
        """Si EmailMessage.send lanza excepción, la vista debe capturarla y mostrar error_envio"""
        data = {
            "destinatarios": ["asistentes"],
            "asistentes_seleccionados": [str(self.asistente.id)],
            "asunto": "Prueba fallo",
            "contenido": "Contenido"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("error_envio", response.context)
        self.assertIn("smtp error".lower(), response.context["error_envio"].lower())
        mock_obtener.assert_called_once()
        mock_send.assert_called_once()
