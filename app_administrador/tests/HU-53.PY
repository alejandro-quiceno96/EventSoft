from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from app_eventos.models import Eventos
from app_administrador.models import Administradores

Usuario = get_user_model()

class EliminarEventoTests(TestCase):
    """Pruebas para la eliminación de eventos por el administrador autorizado."""

    def setUp(self):
        # Cliente de prueba
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

        # Crear evento activo
        self.evento_activo = Eventos.objects.create(
            eve_nombre='Evento Activo',
            eve_descripcion='Evento de prueba activo',
            eve_ciudad='Manizales',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today() + timedelta(days=1),
            eve_estado='Activo',
            eve_capacidad=100,
            eve_imagen='image/test.jpg',
            eve_administrador_fk=self.admin
        )

        # Crear evento cerrado
        self.evento_cerrado = Eventos.objects.create(
            eve_nombre='Evento Cerrado',
            eve_descripcion='Evento ya finalizado',
            eve_ciudad='Pereira',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=date.today() - timedelta(days=3),
            eve_fecha_fin=date.today() - timedelta(days=1),
            eve_estado='Cerrado',
            eve_capacidad=50,
            eve_imagen='image/test2.jpg',
            eve_administrador_fk=self.admin
        )

    def test_eliminar_evento_activo(self):
        """✅ El administrador puede eliminar un evento activo correctamente."""
        url = reverse('administrador:eliminar_evento', args=[self.evento_activo.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Eventos.objects.filter(id=self.evento_activo.id).count(), 0)
        self.assertIn('Evento eliminado correctamente', response.json().get('mensaje', ''))

    def test_no_eliminar_evento_cerrado(self):
        """🚫 No se puede eliminar un evento cerrado."""
        url = reverse('administrador:eliminar_evento', args=[self.evento_cerrado.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Eventos.objects.filter(id=self.evento_cerrado.id).count(), 1)
        self.assertIn('No se puede eliminar un evento cerrado', response.json().get('mensaje', ''))

    def test_metodo_invalido(self):
        """🚫 Solo se permite método POST para eliminar evento."""
        url = reverse('administrador:eliminar_evento', args=[self.evento_activo.id])
        response = self.client.get(url)  # Intento GET en lugar de POST
        self.assertEqual(response.status_code, 405)
        self.assertIn('Método no permitido', response.json().get('mensaje', ''))
