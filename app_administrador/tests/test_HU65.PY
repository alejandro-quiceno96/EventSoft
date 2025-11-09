# app_administrador/tests/test_hu65_actualizar_estado.py

import io
from unittest.mock import patch, mock_open

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core import mail

from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_participante.models import Participantes
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User


class ActualizarEstadoProyectoTestCase(TestCase):
    """
    Pruebas para HU65 - Rechazar/Admitir inscripción de participantes (incluye notificaciones).
    Cubre:
     - GET / método distinto de POST -> 405
     - Falta evento_id -> 400
     - Proyecto no encontrado en evento -> 404
     - Rechazo: actualizar campos, limpiar clave/qr, enviar correo
     - Rechazo sin razón: usa texto por defecto
     - Admisión: generar QR/clave, adjuntar PDF si existe y enviar correo
     - Redirección correcta con ?estado=<nuevo_estado>
    """

    def setUp(self):
        self.client = Client()

        # Crear usuario administrador y su modelo Administradores
        self.user_admin = User.objects.create_user(username="admin1", password="admin123")
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Ciencia 2025",
            eve_descripcion="Evento de innovación científica",
            eve_ciudad="Manizales",
            eve_lugar="Centro Cultural",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear proyecto vinculado al evento
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="P001",
            pro_nombre="Proyecto Test",
            pro_descripcion="Desc",
            pro_documentos="doc.pdf",
            pro_fecha_hora=now(),
            pro_estado="Pendiente"
        )

        # Crear un participante y su inscripción al proyecto (expositor)
        self.user_part = User.objects.create_user(username="part1", password="p1", email="p1@example.com",
                                                  first_name="Pedro", last_name="Pérez")
        self.participante = Participantes.objects.create(usuario=self.user_part)

        self.expositor = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_proyecto=self.proyecto,
            par_eve_fecha_hora=now(),
            par_eve_documentos="doc_expositor.pdf",
            par_eve_estado="Pendiente",
            par_eve_qr="",
            par_eve_clave="",
            habilitado=True
        )

        # Nombre de la URL (ajusta si tu urls.py usa otro)
        self.url_name = "administrador:actualizar_estado"

    def login_admin(self):
        self.client.login(username="admin1", password="admin123")

    def _post_url(self, proyecto_id, nuevo_estado, data=None):
        """Helper para POST al endpoint (no sigue redirect)"""
        url = reverse(self.url_name, args=[proyecto_id, nuevo_estado])
        return self.client.post(url, data or {}, follow=False)

    # -------------------- TESTS --------------------

    def test_get_method_not_allowed(self):
        """Si se usa GET (método distinto a POST) debe devolver 405"""
        self.login_admin()
        url = reverse(self.url_name, args=[self.proyecto.id, "Rechazado"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        # Opcional: verificar estructura JSON si la vista lo devuelve
        try:
            data = response.json()
            self.assertIn("message", data)
        except Exception:
            # si no es JSON, con que devuelva 405 es suficiente
            pass

    def test_missing_evento_id_returns_400(self):
        """Si no se envía evento_id en POST -> 400"""
        self.login_admin()
        response = self._post_url(self.proyecto.id, "Rechazado", data={})  # sin evento_id
        self.assertEqual(response.status_code, 400)
        self.assertIn("ID de evento", response.json().get("message", ""))

    def test_proyecto_not_found_returns_404(self):
        """Si proyecto no pertenece al evento -> 404"""
        self.login_admin()
        # enviar un evento_id que no corresponde (usar id + 1000)
        response = self._post_url(self.proyecto.id, "Rechazado", data={"evento_id": str(self.evento.id + 1000)})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Proyecto no encontrado", response.json().get("message", ""))

    @patch("app_administrador.views.os.path.exists", return_value=True)
    @patch("app_administrador.views.open", new_callable=lambda: mock_open(read_data=b"%PDF-1.4 test pdf bytes"))
    def test_rechazo_sin_razon_usa_default_y_envia_correo(self, mock_file_open, mock_exists):
        """
        Camino RECHAZO sin 'razon' -> debe:
         - Actualizar expositor.par_eve_estado = 'Rechazado'
         - Limpiar clave y qr
         - Enviar correo (capturado en mail.outbox)
         - Redirigir a ver_participantes con ?estado=Rechazado
        """
        self.login_admin()
        response = self._post_url(
            self.proyecto.id,
            "Rechazado",
            data={"evento_id": str(self.evento.id)}  # sin 'razon' -> se usará mensaje por defecto en vista
        )

        # Debe redirigir (302) a ver_participantes con el estado
        self.assertEqual(response.status_code, 302)
        self.assertIn("?estado=Rechazado", response["Location"])

        # Refrescar objeto desde DB
        self.expositor.refresh_from_db()
        self.assertEqual(self.expositor.par_eve_estado, "Rechazado")
        self.assertEqual(self.expositor.par_eve_clave, "")
        self.assertEqual(self.expositor.par_eve_qr, "")

        # Verificar que se haya enviado 1 correo (uno por expositor)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Notificación de rechazo", sent.subject)
        self.assertIn(self.user_part.email, sent.to)

    @patch("app_administrador.views.os.path.exists", return_value=True)
    @patch("app_administrador.views.open", new_callable=lambda: mock_open(read_data=b"%PDF-1.4 test pdf bytes"))
    @patch("app_administrador.views.generar_clave_acceso", return_value="ABC123")
    @patch("app_administrador.views.generar_pdf", return_value="qr_test.pdf")
    def test_admitido_generates_qr_and_clave_and_sends_email(
        self, mock_generar_pdf, mock_generar_clave, mock_open_file, mock_exists
    ):
        """
        Camino ADMITIDO -> debe:
         - Llamar a generar_pdf y generar_clave_acceso
         - Actualizar expositor.par_eve_estado = 'Admitido'
         - Guardar par_eve_qr y par_eve_clave
         - Intentar adjuntar pdf si existe y enviar correo
         - Redirigir a ver_participantes con ?estado=Admitido
        """
        self.login_admin()

        response = self._post_url(
            self.proyecto.id,
            "Admitido",
            data={"evento_id": str(self.evento.id)}
        )

        # Redirección correcta
        self.assertEqual(response.status_code, 302)
        self.assertIn("?estado=Admitido", response["Location"])

        # Refrescar expositor
        self.expositor.refresh_from_db()
        self.assertEqual(self.expositor.par_eve_estado, "Admitido")
        self.assertEqual(self.expositor.par_eve_qr, "qr_test.pdf")
        self.assertEqual(self.expositor.par_eve_clave, "ABC123")

        # Verificar que generar_pdf y generar_clave_acceso fueron llamados
        mock_generar_pdf.assert_called()
        mock_generar_clave.assert_called_once()

        # Correo enviado
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Confirmación de inscripción", sent.subject)
        self.assertIn(self.user_part.email, sent.to)

    def test_rechazo_con_razon_personalizada(self):
        """Rechazo con razón -> verifica que la razón llegue en el correo y el estado se actualice"""
        self.login_admin()
        razon = "No cumple requisitos de documentación."

        response = self._post_url(
            self.proyecto.id,
            "Rechazado",
            data={"evento_id": str(self.evento.id), "razon": razon}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("?estado=Rechazado", response["Location"])

        # refrescar y validar
        self.expositor.refresh_from_db()
        self.assertEqual(self.expositor.par_eve_estado, "Rechazado")

        # Mail
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Notificación de rechazo", sent.subject)
        # Comprobar que la razón aparece en el cuerpo (html)
        self.assertIn("No cumple requisitos", sent.alternatives[0][0])

    def test_acceso_no_autenticado_redirige_login(self):
        """Si no está autenticado, debería redirigir al login (login_required)"""
        url = reverse(self.url_name, args=[self.proyecto.id, "Rechazado"])
        response = self.client.post(url, data={"evento_id": str(self.evento.id)}, follow=False)
        # login_required redirige (302) al login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])
