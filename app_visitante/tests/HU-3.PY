from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario


class EventoDetalleViewTest(TestCase):
    def setUp(self):
        # Crear usuario administrador necesario
        self.usuario = Usuario.objects.create_user(
            username="admin_test",
            password="testpass123",
            tipo_documento="CC",
            documento_identidad="123456789",
        )
        self.admin = Administradores.objects.create(usuario=self.usuario)

        # Iniciar sesión en los tests
        self.client.login(username="admin_test", password="testpass123")

        # Crear un evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Detallado",
            eve_descripcion="Este es un evento de prueba con más detalles.",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio Central",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="Activo",
            eve_imagen="image/evento2.png",
            eve_capacidad=300,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin,
            eve_programacion= "pdf/programacion/evento2.pdf",
        )


    def test_url_evento_detalle_funciona(self):
        """Cada evento debe tener una URL única y funcional"""
        url = reverse("detalle_evento", args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.evento.eve_nombre)
        self.assertContains(response, self.evento.eve_descripcion)

    def test_url_evento_detalle_inexistente(self):
        """Acceder a un evento inexistente debe devolver 404"""
        url = reverse("detalle_evento", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_url_es_compartible(self):
        """La URL generada para un evento debe ser siempre la misma"""
        url1 = reverse("detalle_evento", args=[self.evento.id])
        url2 = reverse("detalle_evento", args=[self.evento.id])
        self.assertEqual(url1, url2)  # determinística
