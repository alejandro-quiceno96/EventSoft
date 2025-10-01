from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app_eventos.models import Eventos
from app_asistente.models import Asistentes
from app_asistente.models import AsistentesEventos

class CompartirEventoTests(TestCase):

    def setUp(self):
        # Crear evento abierto
        self.evento_abierto = Eventos.objects.create(
            eve_nombre="Evento Abierto",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            estado="Abierto"
        )

        # Crear evento cerrado
        self.evento_cerrado = Eventos.objects.create(
            eve_nombre="Evento Cerrado",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            estado="Cerrado"
        )

        # Crear asistente
        self.asistente = Asistentes.objects.create(
            asi_nombre="Carlos",
            asi_correo="carlos@test.com"
        )

        # Crear inscripciones
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento_abierto,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Admitido",
            asi_eve_soporte="pdf/comprobantes/test.pdf",
            asi_eve_qr="pdf/qr_asistentes/test.png",
            asi_eve_clave="1234"
        )

        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento_cerrado,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Admitido",
            asi_eve_soporte="pdf/comprobantes/test.pdf",
            asi_eve_qr="pdf/qr_asistentes/test.png",
            asi_eve_clave="5678"
        )

    def test_compartir_visible_evento_abierto(self):
        url = reverse("asistente_inscripciones", args=[self.asistente.id])
        response = self.client.get(url)

        # El botón de compartir debe aparecer en el evento abierto
        self.assertContains(response, "Compartir")

    def test_compartir_oculto_evento_cerrado(self):
        url = reverse("asistente_inscripciones", args=[self.asistente.id])
        response = self.client.get(url)

        # El evento cerrado no debe mostrar el botón de compartir
        self.assertNotContains(response, "Compartir no disponible", status_code=200)
