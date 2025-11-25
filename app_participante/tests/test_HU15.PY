from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_eventos.models import Eventos
import datetime
from app_administrador.models import Administradores

class PreinscripcionParticipanteViewTest(TestCase):

    def setUp(self):
        self.client = Client()

        # 🔹 Evitar duplicados si ya existen los usuarios
        Usuario.objects.filter(username="participante_test").delete()
        Usuario.objects.filter(username="admin_test").delete()

        # Crear usuario normal (visitante/participante)
        self.usuario_participante = Usuario.objects.create_user(
            username="participante_test",
            email="participante@test.com",
            password="test12345",
            tipo_documento="CC",
            documento_identidad="2222",
            telefono="3010000000"
        )

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

        # URL a probar
        self.url = reverse('preinscripcion_participante', args=[self.evento.id])

    def test_login_required_redirects(self):
        """La vista debe redirigir al login si no hay sesión activa."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_view_loads_correctly_for_logged_user(self):
        """La vista debe cargar correctamente para un usuario autenticado."""
        # 🔹 Iniciar sesión con el participante
        logged_in = self.client.login(username='participante_test', password='test12345')
        self.assertTrue(logged_in, "El inicio de sesión falló en el test")

        # 🔹 Hacer la petición
        response = self.client.get(self.url)

        # 🔹 Verificar que la vista cargue correctamente
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/Pre_inscripcion_participante.html')
        self.assertContains(response, self.evento.eve_nombre)
