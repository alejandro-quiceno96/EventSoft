from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from datetime import date
from app_eventos.models import Eventos, ParticipantesEventos
from app_administrador.models import Administradores
from app_participante.models import Participantes
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ParticipantesPendientesTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = User.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9999",
            telefono="3100000000"
        )

        # Crear administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=1,
            estado="Activo",
            clave_acceso="CLVADMIN"
        )

        # Forzar login
        self.client.force_login(self.usuario_admin)
        documento_fake = SimpleUploadedFile(
        "doc1.pdf",
        b"Contenido de prueba del documento",
        content_type="application/pdf"
)
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Tecnología",
            eve_descripcion="Evento de innovación",
            eve_ciudad="Manizales",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=date(2025, 10, 1),
            eve_fecha_fin=date(2025, 10, 3),
            eve_estado="Activo",
            eve_imagen="image/test.jpg",
            eve_capacidad=100,
            eve_administrador_fk=self.admin
        )

        # Crear participantes (usuarios)
        self.usuario_part1 = User.objects.create_user(
            username='part1',
            password='12345',
            first_name='Pedro',
            email='pedro@example.com'
        )
        self.participante1 = Participantes.objects.create(usuario=self.usuario_part1)

        self.usuario_part2 = User.objects.create_user(
            username='part2',
            password='12345',
            first_name='Ana',
            email='ana@example.com'
        )
        self.participante2 = Participantes.objects.create(usuario=self.usuario_part2)

        self.usuario_part3 = User.objects.create_user(
            username='part3',
            password='12345',
            first_name='Luis',
            email='luis@example.com'
        )
        self.participante3 = Participantes.objects.create(usuario=self.usuario_part3)

        # Crear ParticipantesEventos con diferentes estados
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante1,
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión",
            par_eve_documentos=documento_fake,
            par_eve_fecha_hora=date.today(),
            par_eve_clave="X123"
        )

        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante2,
            par_eve_evento_fk=self.evento,
            par_eve_estado="Admitido",
            par_eve_documentos=documento_fake,
            par_eve_fecha_hora=date.today(),
            par_eve_clave="Y456"
        )

        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante3,
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión",
            par_eve_documentos=documento_fake,
            par_eve_fecha_hora=date.today(),
            par_eve_clave="Z789"
        )

    def test_listado_participantes_pendientes(self):
        """Verifica que solo se listan los participantes con estado 'Pendiente de Revisión'"""
        pendientes = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión"
        )

        self.assertEqual(pendientes.count(), 2)
        estados = [p.par_eve_estado for p in pendientes]
        self.assertTrue(all(e == "Pendiente de Revisión" for e in estados))

    def test_descarga_documentos_autenticada(self):
        """Verifica que la descarga de documentos requiere autenticación"""
        pendientes = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión"
        )
        participante = pendientes.first()

        # Suponiendo que existe una URL para descargar documentos como:
        # path('participante/<int:participante_id>/documento/', views.descargar_documento, ...)
        download_url = f"/administrador/participante/{participante.id}/documento/"

        # Sin login
        self.client.logout()
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 302)  # Redirige al login

        # Con login
        self.client.force_login(self.usuario_admin)
        response = self.client.get(download_url)
        # Aquí asumimos que la vista devuelve 200 si el documento existe
        self.assertEqual(response.status_code, 200)
