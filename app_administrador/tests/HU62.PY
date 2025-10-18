from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, EvaluadoresEventos
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime
from app_administrador.models import Administradores
from app_evaluador.models import Evaluadores
class EvaluadoresPendientesTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )

        # Crear administrador asociado
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # Loguear como administrador
        self.client.force_login(self.usuario_admin)
        # Crear evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test',
            eve_descripcion='Desc test',
            eve_ciudad='Caldas',
            eve_lugar='Manizales',
            eve_fecha_inicio=datetime.date(2025, 10, 10),
            eve_fecha_fin=datetime.date(2025, 10, 12),
            eve_estado='Activo',
            eve_imagen='image/test.jpg',
            eve_capacidad=100,
            eve_administrador_fk=self.admin,
        )

        # Crear documento falso
        documento = SimpleUploadedFile("documento.pdf", b"contenido de prueba", content_type="application/pdf")

        self.evaluador = Evaluadores.objects.create(
            eva_cedula='123456789',
            eva_nombre='Juan Pérez',
            eva_correo='juanperez@example.com',
            eva_telefono='3120000000'
        )

        # Crear documento simulado
        documento = SimpleUploadedFile("documento.pdf", b"contenido de prueba", content_type="application/pdf")

        # Crear evaluador pendiente de revisión
        self.evaluador_pendiente = EvaluadoresEventos.objects.create(
            eva_eve_evento_fk=self.evento,
            eva_eve_evaluador_fk=self.evaluador,  # 👈 Aquí se corrige
            eva_estado='Pendiente de Revisión',
            eva_eve_documentos=documento
        )

    def test_listado_evaluadores_pendientes(self):
        """Verifica que se muestren evaluadores en estado Pendiente de Revisión"""
        response = self.client.get(reverse('evaluadores_pendientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pendiente de Revisión')
        self.assertIn(self.evaluador_pendiente, response.context['evaluadores'])

    def test_descarga_documentos_autenticada(self):
        """Verifica que la descarga de documentos requiere autenticación"""
        self.client.logout()
        download_url = reverse('descargar_documento_evaluador', args=[self.evaluador_pendiente.id])
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 302)  # Redirige a login
        self.client.login(username='admin_test', password='12345')
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)

    def test_aprobar_evaluador(self):
        """Verifica que el administrador puede aprobar un evaluador"""
        url = reverse('aprobar_evaluador', args=[self.evaluador_pendiente.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.evaluador_pendiente.refresh_from_db()
        self.assertEqual(self.evaluador_pendiente.eva_estado, 'Aprobado')

    def test_rechazar_evaluador(self):
        """Verifica que el administrador puede rechazar un evaluador"""
        url = reverse('rechazar_evaluador', args=[self.evaluador_pendiente.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.evaluador_pendiente.refresh_from_db()
        self.assertEqual(self.evaluador_pendiente.eva_estado, 'Rechazado')
