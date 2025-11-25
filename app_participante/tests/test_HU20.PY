from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import make_aware
from datetime import datetime
from io import BytesIO

from app_eventos.models import Eventos, ParticipantesEventos
from app_participante.models import Participantes
from app_usuarios.models import Usuario
from app_administrador.models import Administradores


class ProgramacionEventoTest(TestCase):
    """HU-20: Visualizar y descargar programación del evento (Participante)"""

    def setUp(self):
        """Configuración inicial de datos"""
        self.client = Client()

        # Crear usuario administrador y su perfil
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

        # Crear usuario participante
        self.user = Usuario.objects.create_user(
            username='participante1',
            password='12345',
            tipo_documento='CC',
            documento_identidad='2222',
            telefono='3010000000'
        )
        self.participante = Participantes.objects.create(usuario=self.user)

        # Crear PDF simulado para ambos eventos
        pdf_content1 = BytesIO(b"%PDF-1.4 Simulated PDF content 1")
        pdf_file1 = SimpleUploadedFile("programacion.pdf", pdf_content1.getvalue(), content_type="application/pdf")

        pdf_content2 = BytesIO(b"%PDF-1.4 Simulated PDF content 2")
        pdf_file2 = SimpleUploadedFile("programacion2.pdf", pdf_content2.getvalue(), content_type="application/pdf")

        # Crear evento admitido
        self.evento_admitido = Eventos.objects.create(
            eve_nombre="Evento Admitido",
            eve_descripcion="Evento con acceso permitido",
            eve_ciudad="Bogotá",
            eve_lugar="Centro",
            eve_fecha_inicio="2025-11-01",
            eve_fecha_fin="2025-11-03",
            eve_estado="Activo",
            eve_imagen="image/evento.jpg",
            eve_capacidad=100,
            eve_programacion=pdf_file1,
            eve_administrador_fk=self.admin
        )

        # Crear evento rechazado
        self.evento_rechazado = Eventos.objects.create(
            eve_nombre="Evento No Admitido",
            eve_descripcion="Evento sin acceso",
            eve_ciudad="Medellín",
            eve_lugar="Plaza Mayor",
            eve_fecha_inicio="2025-12-01",
            eve_fecha_fin="2025-12-03",
            eve_estado="Activo",
            eve_imagen="image/evento2.jpg",
            eve_capacidad=50,
            eve_programacion=pdf_file2,
            eve_administrador_fk=self.admin
        )

        # Crear participación admitida
        self.participacion_admitida = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento_admitido,
            par_eve_estado="Admitido",
            par_eve_fecha_hora=make_aware(datetime(2025, 10, 1, 10, 0)),
            par_eve_documentos="pdf/proyectos/test.pdf",
            par_eve_qr="pdf/qr_participante/qr.png",
            par_eve_clave="123ABC",
            habilitado=True
        )

        # Crear participación rechazada
        self.participacion_rechazada = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento_rechazado,
            par_eve_estado="Rechazado",
            par_eve_fecha_hora=make_aware(datetime(2025, 10, 1, 10, 0)),
            par_eve_documentos="pdf/proyectos/test.pdf",
            par_eve_qr="pdf/qr_participante/qr.png",
            par_eve_clave="456DEF",
            habilitado=True
        )

        # Iniciar sesión del participante
        self.client.login(username='participante1', password='12345')

        # URL que carga los eventos del participante
        self.url_eventos = reverse('app_participante:ver_info_participante')

    # ------------------------------------------------------------
    # PRUEBAS
    # ------------------------------------------------------------

    def test_visualizar_eventos(self):
        """✅ Debe mostrar tanto los eventos inscritos como sus estados"""
        response = self.client.get(self.url_eventos)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Se debe renderizar el nombre del evento admitido
        self.assertIn(self.evento_admitido.eve_nombre, content)

        # También debe aparecer el evento rechazado
        self.assertIn(self.evento_rechazado.eve_nombre, content)

        # Además debe mostrar los estados visualmente
        self.assertIn("Admitido", content)
        self.assertIn("Rechazado", content)


    def test_acceso_evento_no_admitido_denegado(self):
        """🚫 No debe permitir acceder a programación de evento no admitido"""
        pdf_url = self.evento_rechazado.eve_programacion.url
        response = self.client.get(pdf_url)
        self.assertIn(response.status_code, [403, 404])

    def test_login_requerido(self):
        """🚫 Debe exigir inicio de sesión para acceder a los eventos"""
        self.client.logout()
        response = self.client.get(self.url_eventos)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)
