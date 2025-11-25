from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from django.utils import timezone
from app_eventos.models import Eventos, ParticipantesEventos
from app_participante.models import Participantes
from app_administrador.models import Administradores
from app_criterios.models import Criterios

User = get_user_model()

class HU24InstrumentoEvaluacionTestCase(TestCase):
    """HU24 - El participante puede acceder al instrumento de evaluación del evento si está inscrito"""

    def setUp(self):
        self.user = User.objects.create_user(username='expo', password='12345')
        self.participante = Participantes.objects.create(usuario=self.user)

        self.admin_user = User.objects.create_user(username='admin', password='admin123')
        self.admin = Administradores.objects.create(usuario=self.admin_user)

        self.evento = Eventos.objects.create(
            eve_nombre='Expo Innovación',
            eve_descripcion='Evento para evaluación de proyectos',
            eve_ciudad='Bogotá',
            eve_lugar='Corferias',
            eve_fecha_inicio=date(2025, 11, 1),
            eve_fecha_fin=date(2025, 11, 3),
            eve_estado='Activo',
            eve_imagen='img/test.png',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        Criterios.objects.create(cri_descripcion='Claridad del proyecto', cri_peso=50, cri_evento_fk=self.evento)
        Criterios.objects.create(cri_descripcion='Innovación', cri_peso=50, cri_evento_fk=self.evento)

        self.client = Client()
        self.client.login(username='expo', password='12345')
        self.url = reverse('app_participante:generar_pdf_criterios', kwargs={'evento_id': self.evento.id})

    def test_participante_inscrito_puede_ver_instrumento(self):
        ParticipantesEventos.objects.create(
            par_eve_evento_fk=self.evento,
            par_eve_participante_fk=self.participante,
            par_eve_fecha_hora=timezone.now(),
            par_eve_estado='Admitido',
            par_eve_clave='ABC123',
            par_eve_qr='pdf/qr/test.pdf',
            par_eve_documentos='pdf/doc.pdf'
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'criterios_evaluacion_{self.evento.eve_nombre}', response['Content-Disposition'])

