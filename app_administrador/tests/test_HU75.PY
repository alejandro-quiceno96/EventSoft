from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from django.utils.timezone import now
from app_usuarios.models import Usuario as User


class SubirInfoTecnicaTestCase(TestCase):
    def setUp(self):
        # Crear usuario administrador
        self.user_admin = User.objects.create_user(
            username='admin1',
            password='admin123',
            first_name='Carlos',
            last_name='López',
            is_staff=True
        )
        self.admin = Administradores.objects.create(
            usuario=self.user_admin
        )

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Criterios",
            eve_descripcion="Prueba HU74",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="img.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        self.client = Client()
        self.client.login(username='admin1', password='admin123')

    def test_subida_exitosa_archivo(self):
        """POST con archivo válido debe actualizar el evento"""
        archivo = SimpleUploadedFile("info_tecnica.pdf", b"contenido del pdf")
        url = reverse('administrador:subir_info_tecnica', args=[self.evento.id])
        response = self.client.post(url, {'eve_informacion_tecnica': archivo})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        evento_actualizado = get_object_or_404(Eventos, pk=self.evento.id)
        self.assertTrue(bool(evento_actualizado.eve_informacion_tecnica))

    def test_post_sin_archivo(self):
        """POST sin archivo devuelve error 400"""
        url = reverse('administrador:subir_info_tecnica', args=[self.evento.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False})

    def test_get_no_permitido(self):
        """GET devuelve error 400"""
        url = reverse('administrador:subir_info_tecnica', args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False})

    def test_evento_no_existente(self):
        """Evento inexistente devuelve 404"""
        url = reverse('administrador:subir_info_tecnica', args=[9999])
        response = self.client.post(url, {'eve_informacion_tecnica': SimpleUploadedFile("archivo.pdf", b"contenido")})
        self.assertEqual(response.status_code, 404)
