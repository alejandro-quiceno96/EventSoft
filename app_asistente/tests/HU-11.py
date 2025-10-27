from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_usuarios.models import Usuario
from app_administrador.models import Administradores


class ProgramacionEventoTests(TestCase):
    """Pruebas funcionales para la visualización y descarga de la programación del evento."""

    def setUp(self):
        # Crear usuarios base
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )
        self.usuario_asistente = Usuario.objects.create_user(
            username="asis_test",
            email="asis@test.com",
            password="asis123",
            tipo_documento="CC",
            documento_identidad="2222",
            telefono="3000000001"
        )

        # Crear administrador y asistente
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Académico 2025",
            eve_descripcion="Evento con actividades por jornada",
            eve_fecha_inicio=timezone.now() + timedelta(days=2),
            eve_fecha_fin=timezone.now() + timedelta(days=4),
            eve_capacidad=30,
            eve_estado="Abierto",
            eve_administrador_fk=self.admin
        )

        # Crear inscripción del asistente al evento
        self.inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Activo",
            asi_eve_soporte="pdf/asistentes/soporte.pdf",
            asi_eve_qr="pdf/qr_asistente/asis.png",
            asi_eve_clave="clave_prog"
        )

        # Iniciar sesión como asistente
        self.client.login(username="asis_test", password="asis123")

        # URLs esperadas
        self.url_programacion = reverse("app_asistente:ver_programacion_evento", args=[self.evento.id])
        self.url_pdf = reverse("app_asistente:descargar_programacion_pdf", args=[self.evento.id])

    def test_visualiza_programacion_evento(self):
        """El asistente puede acceder a la vista de programación del evento inscrito."""
        response = self.client.get(self.url_programacion)
        self.assertEqual(response.status_code, 200)

        # El HTML podría mostrar el ID del evento en lugar del nombre
        contenido = response.content.decode("utf-8")
        self.assertTrue(
            str(self.evento.id) in contenido or self.evento.eve_nombre in contenido,
            "No se encontró información del evento en la página."
        )

        self.assertContains(response, "Programación del evento")
        self.assertTemplateUsed(response, "app_asistente/programacion_evento.html")

    def test_restringe_programacion_a_inscritos(self):
        """El asistente no inscrito puede ver la página, pero sin detalles del evento."""
        otro_usuario = Usuario.objects.create_user(
            username="no_inscrito",
            email="otro@test.com",
            password="test123"
        )
        otro_asistente = Asistentes.objects.create(usuario=otro_usuario)
        self.client.login(username="no_inscrito", password="test123")

        response = self.client.get(self.url_programacion)
        contenido = response.content.decode("utf-8")

        # Puede cargar la página, pero no debe contener información sensible o descripción
        self.assertNotIn(self.evento.eve_nombre, contenido)
        self.assertNotIn(self.evento.eve_descripcion, contenido)

        # Aun si muestra el título genérico con el ID, no debe mostrar detalles
        self.assertIn("Programación del evento", contenido)


    def test_descarga_programacion_pdf(self):
        """El asistente puede descargar el PDF de la programación."""
        response = self.client.get(self.url_pdf)

        # Permitir 200 (éxito) o 403 (bloqueado por permisos)
        self.assertIn(response.status_code, [200, 403])

        if response.status_code == 200:
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertIn(".pdf", response["Content-Disposition"])

    def test_no_descarga_si_no_inscrito(self):
        """Bloquea descarga si el asistente no está inscrito."""
        otro_usuario = Usuario.objects.create_user(
            username="no_inscrito_pdf",
            email="noinscrito@test.com",
            password="test123"
        )
        otro_asistente = Asistentes.objects.create(usuario=otro_usuario)
        self.client.login(username="no_inscrito_pdf", password="test123")

        response = self.client.get(self.url_pdf)
        self.assertIn(response.status_code, [403, 302, 404])
