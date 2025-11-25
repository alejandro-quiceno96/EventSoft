from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
import tempfile

from app_eventos.models import Eventos, EventosCategorias,Proyecto, ParticipantesEventos
from app_categorias.models import Categorias
from app_participante.models import Participantes
from app_administrador.models import Administradores
from app_areas.models import Areas
from app_usuarios.models import Usuario


class EventoDetalleParticipanteTestCase(TestCase):

    def setUp(self):
        # Cliente autenticado
        self.client = Client()
        self.user = Usuario.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        # Administrador (FK requerida por Evento)
        self.admin = Administradores.objects.create(usuario=self.user)

        # Archivos temporales para campos FileField / ImageField
        self.temp_image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        self.temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf").name

        # Crear Área y Categoría
        self.area = Areas.objects.create(are_nombre="Ciencias Naturales")
        self.categoria = Categorias.objects.create(
            cat_nombre="Investigación",
            cat_descripcion="Categoría de prueba",
            cat_area_fk=self.area
        )

        # Crear Evento
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Ciencia",
            eve_descripcion="Evento de ciencia y tecnología",
            eve_ciudad="Bogotá",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today(),
            eve_estado="Activo",
            eve_imagen=self.temp_image,
            eve_capacidad=100,
            eve_tienecosto=True,
            eve_programacion=self.temp_pdf,
            eve_informacion_tecnica=self.temp_pdf,
            eve_administrador_fk=self.admin
        )

        # Relación Evento-Categoría
        self.evento_categoria = EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento,
            eve_cat_categoria_fk=self.categoria
        )

        # Crear Participante
        self.participante = Participantes.objects.create(usuario=self.user)

        # Crear Proyecto (ahora con FK a Evento)
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PRJ-001",
            pro_nombre="Proyecto de prueba",
            pro_descripcion="Descripción del proyecto",
            pro_documentos=self.temp_pdf,
            pro_estado="Aprobado"
        )

        # Crear ParticipanteEvento (inscripción)
        self.participante_evento = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=self.temp_pdf,
            par_eve_estado="Aprobado",
            par_eve_qr=self.temp_pdf,
            par_eve_clave="CLAVE123",
            par_eve_proyecto=self.proyecto
        )

        # URL de la vista
        self.url = reverse(
            'app_participante:detalle_evento',
            kwargs={'evento_id': self.evento.id, 'participante_id': self.participante.id}
        )

    def test_evento_detalle_participante_exitoso(self):
        """✅ Debe retornar los datos del evento y del participante en formato JSON"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validar datos principales
        self.assertEqual(data['eve_nombre'], self.evento.eve_nombre)
        self.assertEqual(data['eve_categoria'], self.categoria.cat_nombre)
        self.assertEqual(data['eve_clave'], self.participante_evento.par_eve_clave)
        self.assertEqual(data['eve_costo'], 'Con Pago')
        self.assertEqual(data['proyecto'], self.proyecto.pro_codigo)
        self.assertIn("Centro de Convenciones", data['eve_lugar'])

        # Validar existencia de claves esperadas en el JSON
        expected_keys = {
            'eve_id', 'eve_nombre', 'eve_descripcion', 'eve_ciudad',
            'eve_lugar', 'eve_fecha_inicio', 'eve_fecha_fin', 'eve_estado',
            'eve_categoria', 'eve_clave', 'codigo_qr', 'proyecto'
        }
        self.assertTrue(expected_keys.issubset(data.keys()))

    def test_evento_no_encontrado(self):
        """🚫 Debe devolver 404 si el evento no existe"""
        url = reverse('app_participante:detalle_evento', kwargs={'evento_id': 9999, 'participante_id': self.participante.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
