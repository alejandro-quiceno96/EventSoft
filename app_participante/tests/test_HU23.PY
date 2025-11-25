from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from app_eventos.models import Eventos, ParticipantesEventos
from app_participante.models import Participantes
from app_administrador.models import Administradores

User = get_user_model()

class InformacionTecnicaEventoTestCase(TestCase):
    """HU23: Como EXPONENTE, quiero acceder a la información técnica de las actividades en las que participo."""

    def setUp(self):
        # --- Crear participante ---
        self.user = User.objects.create_user(
            username='expo1',
            password='12345',
            first_name='Carlos',
            last_name='Lopez',
            email='carlos@example.com'
        )
        self.participante = Participantes.objects.create(usuario=self.user)

        # --- Crear administrador ---
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            first_name='Admin',
            last_name='Prueba',
            email='admin@example.com'
        )
        self.administrador = Administradores.objects.create(usuario=self.admin_user)

        # --- Crear archivos temporales ---
        self.temp_pdf = SimpleUploadedFile("test.pdf", b"contenido de prueba", content_type="application/pdf")
        self.temp_qr = SimpleUploadedFile("test_qr.png", b"imagen falsa", content_type="image/png")

        # --- Crear evento ---
        self.evento = Eventos.objects.create(
            eve_nombre='Congreso Nacional',
            eve_descripcion='Evento de prueba para exponentes',
            eve_ciudad='Bogotá',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio=date(2025, 11, 1),
            eve_fecha_fin=date(2025, 11, 3),
            eve_estado='Activo',
            eve_imagen=self.temp_qr,
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_informacion_tecnica=self.temp_pdf
        )

        # --- Crear cliente autenticado ---
        self.client = Client()
        self.client.login(username='expo1', password='12345')

        # URL del detalle del evento
        self.url = reverse(
            'app_participante:detalle_evento',
            kwargs={'evento_id': self.evento.id, 'participante_id': self.participante.id}
        )

    # --------------------------------------------------------------
    # ✅ TEST 1: Participante inscrito puede acceder a la información técnica
    # --------------------------------------------------------------
    def test_participante_inscrito_puede_ver_informacion_tecnica(self):
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_estado="Admitido",
            par_eve_qr=self.temp_qr,
            par_eve_documentos=self.temp_pdf,
            par_eve_clave="CLAVE123"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()  # ✅ leer el JsonResponse
        self.assertIn("eve_informacion_tecnica", data)
        self.assertTrue(data["eve_informacion_tecnica"].endswith(".pdf"))

    # --------------------------------------------------------------
    # ❌ TEST 2: Participante NO inscrito no puede acceder
    # --------------------------------------------------------------
    def test_participante_no_inscrito_no_puede_ver_informacion_tecnica(self):
        response = self.client.get(self.url)

        # Puede ser redirección (302), prohibido (403) o no encontrado (404)
        self.assertIn(response.status_code, [302, 403, 404])


    # --------------------------------------------------------------
    # ✅ TEST 3: La información técnica aparece correctamente en el JSON
    # --------------------------------------------------------------
    def test_informacion_tecnica_en_json_correcta(self):
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_estado='Admitido',
            par_eve_qr=self.temp_qr,
            par_eve_documentos=self.temp_pdf
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["eve_nombre"], "Congreso Nacional")
        self.assertIn(".pdf", data["eve_informacion_tecnica"])
