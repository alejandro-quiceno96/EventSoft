from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from django.utils import timezone
from django.utils.timezone import now

from app_eventos.models import Eventos, EvaluadoresEventos
from app_evaluador.models import Evaluadores
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User

class ActualizarEstadoEvaluadorTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.user_admin = User.objects.create_user(username="admin", password="admin123")
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Test",
            eve_descripcion="Descripción",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="image.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear evaluador
        self.user_eval = User.objects.create_user(
            username="eval1",
            password="1234",
            first_name="Laura",
            last_name="Ríos",
            email="laura@example.com"
        )
        self.evaluador = Evaluadores.objects.create(usuario=self.user_eval)

        # Relación Evaluador-Evento
        self.evaluador_evento = EvaluadoresEventos.objects.create(
            eva_eve_evento_fk=self.evento,
            eva_eve_evaluador_fk=self.evaluador,
            eva_estado="Pendiente"
        )

        self.url = reverse('administrador:actualizar_estado_evaluador',
                           args=[self.evaluador.id, 'Admitido'])
        self.client.login(username="admin", password="admin123")

    def test_metodo_no_permitido(self):
        """CA1: Retorna error 405 si se usa método GET"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Método no permitido", response.json()["message"])

    def test_evento_id_no_enviado(self):
        """CA2: Retorna error 400 si no se envía evento_id"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("ID de evento no proporcionado", response.json()["message"])

    def test_evaluador_no_encontrado(self):
        """CA3: Retorna error 404 si el evaluador no está en el evento"""
        # Creamos un evaluador que existe pero NO está asociado al evento
        otro_user = User.objects.create_user(username="evalX", password="1234")
        otro_eval = Evaluadores.objects.create(usuario=otro_user)

        response = self.client.post(
            reverse('administrador:actualizar_estado_evaluador', args=[otro_eval.id, 'Admitido']),
            {'evento_id': self.evento.id}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Evaluador no encontrado", response.json()["message"])

    @patch("app_administrador.views.generar_pdf", return_value="pdfs/qr_test.pdf")
    @patch("app_administrador.views.generar_clave_acceso", return_value="ABC123")
    @patch("app_administrador.views.EmailMultiAlternatives.send", return_value=True)
    def test_actualizacion_estado_admitido(self, mock_send, mock_clave, mock_pdf):
        """CA4: Flujo correcto al admitir evaluador"""
        response = self.client.post(
            self.url,
            {'evento_id': self.evento.id}
        )
        self.assertEqual(response.status_code, 302)  # Redirección
        self.evaluador_evento.refresh_from_db()
        self.assertEqual(self.evaluador_evento.eva_estado, "Admitido")
        mock_send.assert_called_once()

    @patch("app_administrador.views.EmailMultiAlternatives.send", return_value=True)
    def test_actualizacion_estado_rechazado(self, mock_send):
        """CA5: Flujo correcto al rechazar evaluador"""
        url = reverse('administrador:actualizar_estado_evaluador',
                      args=[self.evaluador.id, 'Rechazado'])
        response = self.client.post(
            url,
            {'evento_id': self.evento.id, 'motivo': 'Perfil no adecuado'}
        )
        self.assertEqual(response.status_code, 302)
        self.evaluador_evento.refresh_from_db()
        self.assertEqual(self.evaluador_evento.eva_estado, "Rechazado")
        mock_send.assert_called_once()
