from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from app_usuarios.models import Usuario
from app_asistente.models import Asistentes
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores


class RegistroPagoSoporteTest(TestCase):
    def setUp(self):
        # Usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            password="testpass123",
            tipo_documento="CC",
            documento_identidad="99999999"
        )
        self.admin = Administradores.objects.create(usuario=self.usuario_admin)

        # Evento con costo
        self.evento = Eventos.objects.create(
            eve_nombre="Evento con Costo",
            eve_descripcion="Evento que requiere pago",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="Activo",
            eve_imagen="image/evento_pago.png",
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin,
            eve_programacion="pdf/programacion/evento_pago.pdf"
        )

        # Usuario asistente
        self.usuario = Usuario.objects.create_user(
            username="asistente_test",
            password="testpass123",
            tipo_documento="CC",
            documento_identidad="12345678",
        )
        self.asistente = Asistentes.objects.create(usuario=self.usuario)
        self.client.login(username="asistente_test", password="testpass123")

        # Preinscripción inicial
        self.inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Pendiente"
        )

    def test_subida_exitosa_soporte(self):
        """Debe aceptar PDF válido y cambiar estado a 'Pendiente de Validación'"""
        archivo = SimpleUploadedFile("comprobante.pdf", b"archivo_contenido", content_type="application/pdf")
        url = reverse("registrar_asistente", args=[self.evento.id])
        response = self.client.post(url, {"soporte": archivo})

        self.inscripcion.refresh_from_db()
        self.assertEqual(response.status_code, 302)  # Redirección tras subida
        self.assertEqual(self.inscripcion.asi_eve_estado, "Pendiente")
        self.assertRedirects( response, reverse("inicio_visitante") + "?registro=exito_asistente")
