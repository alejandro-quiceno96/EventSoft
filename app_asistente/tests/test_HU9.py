from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores
from app_usuarios.models import Usuario


class CompartirEventoTests(TestCase):

    def setUp(self):
        # === Crear usuario administrador ===
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            password="admin123",
            first_name="Admin",
            last_name="Test",
            tipo_documento="CC",
            documento_identidad="1001",
            email="admin@test.com",
            telefono="3001234567"
        )

        # Crear administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=0,
            estado="Activo",
            clave_acceso="ABCD1234"
        )

        # === Crear usuario asistente ===
        self.usuario_asistente = Usuario.objects.create_user(
            username="carlos_test",
            password="carlos123",
            first_name="Carlos",
            last_name="Gómez",
            tipo_documento="CC",
            documento_identidad="2002",
            email="carlos@test.com",
            telefono="3019876543"
        )

        # Crear asistente vinculado al usuario
        self.asistente = Asistentes.objects.create(
            usuario=self.usuario_asistente
        )

        # === Crear eventos ===
        self.evento_abierto = Eventos.objects.create(
            eve_nombre="Evento Abierto",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Abierto",
            eve_capacidad=50,
            eve_administrador_fk=self.admin
        )

        self.evento_cerrado = Eventos.objects.create(
            eve_nombre="Evento Cerrado",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Cerrado",
            eve_capacidad=0,
            eve_administrador_fk=self.admin
        )

        # === Crear inscripciones ===
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

    # === TESTS ===

    def test_compartir_visible_evento_abierto(self):
        """El botón de compartir debe ser visible para eventos abiertos."""
        url = reverse("app_asistente:asistente_inscripciones")


        response = self.client.get(url)
        self.assertContains(response, "Compartir")

    def test_compartir_oculto_evento_cerrado(self):
        """El botón de compartir debe estar oculto o desactivado para eventos cerrados."""
        url = reverse("app_asistente:asistente_inscripciones")


        response = self.client.get(url)
        self.assertNotIn('data-bs-target="#modalCompartir"', response.content.decode(),
                 "El evento cerrado no debería mostrar el botón de compartir activo")

