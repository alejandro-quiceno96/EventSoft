from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_evaluador.models import Evaluadores
from app_usuarios.models import Usuario as User


class SubirInformacionTecnicaTestCase(TestCase):
    """HU-43: El evaluador carga la información técnica del evento"""

    def setUp(self):
        # Crear usuario y administrador
        self.user = User.objects.create_user(username="admin", password="12345")
        self.admin = Administradores.objects.create(usuario=self.user)

        # Crear evaluador
        self.user_eval = User.objects.create_user(username="eval", password="12345")
        self.evaluador = Evaluadores.objects.create(
            usuario=self.user_eval,
        )

        # Crear evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre="Feria Científica 2025",
            eve_descripcion="Evento de ciencia y tecnología",
            eve_ciudad="Manizales",
            eve_lugar="Recinto del Pensamiento",
            eve_fecha_inicio="2025-11-10",
            eve_fecha_fin="2025-11-12",
            eve_estado="Activo",
            eve_imagen="image/test.png",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        self.client = Client()
        self.url = reverse('app_evaluador:subir_info_tecnica', args=[self.evento.id])

    # ---------------- CA1 ----------------
    def test_subir_info_tecnica_exitosamente(self):
        """CA1: El evaluador puede cargar correctamente el archivo de información técnica"""
        archivo = SimpleUploadedFile(
            "info_tecnica.pdf", b"contenido de prueba", content_type="application/pdf"
        )

        data = {
            'cedula': self.evaluador.id,
            'eve_informacion_tecnica': archivo
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirección exitosa

    # ---------------- CA2 ----------------
    def test_error_sin_cedula(self):
        """CA2: Retorna error cuando no se envía el id del evaluador"""
        archivo = SimpleUploadedFile(
            "info_tecnica.pdf", b"contenido de prueba", content_type="application/pdf"
        )
        data = {'eve_informacion_tecnica': archivo}
        response = self.client.post(self.url, data)
        self.assertJSONEqual(
            response.content,
            {'success': False, 'message': 'No se pudo identificar al evaluador.'}
        )

    # ---------------- CA3 ----------------
    def test_error_sin_archivo(self):
        """CA3: Retorna error cuando no se adjunta archivo"""
        data = {'cedula': self.evaluador.id}
        response = self.client.post(self.url, data)
        self.assertJSONEqual(
            response.content,
            {'success': False, 'message': 'No se encontró el archivo a subir.'}
        )

    # ---------------- CA4 ----------------
    def test_error_metodo_no_permitido(self):
        """CA4: Retorna error al usar GET en lugar de POST"""
        response = self.client.get(self.url)
        self.assertJSONEqual(
            response.content,
            {'success': False, 'message': 'Método no permitido.'}
        )
