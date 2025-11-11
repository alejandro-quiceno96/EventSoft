from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_categorias.models import Categorias
from app_areas.models import Areas
from django.core.files.uploadedfile import SimpleUploadedFile

Usuario = get_user_model()

class EventoRestriccionesTests(TestCase):
    """Pruebas para validar restricciones clave del evento (HU50)."""

    def setUp(self):
        # Imagen simulada
        self.imagen_fake = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )

        # Usuario y administrador
        self.user = Usuario.objects.create_user(
            username="admin",
            password="12345",
            email="admin@test.com"
        )
        self.administrador = Administradores.objects.create(usuario=self.user)

        # Área y categoría
        self.area = Areas.objects.create(
            are_nombre="Ciencias de la Computación",
            are_descripcion="Área relacionada con la informática y tecnología"
        )
        self.categoria = Categorias.objects.create(
            cat_nombre="Tecnología",
            cat_descripcion="Eventos relacionados con tecnología",
            cat_area_fk=self.area
        )

        # Evento base
        self.evento = Eventos.objects.create(
        eve_nombre="Congreso de Prueba",
        eve_descripcion="Evento para test de restricciones",
        eve_ciudad="Manizales",
        eve_lugar="Auditorio Principal",
        eve_fecha_inicio=date.today() + timedelta(days=30),
        eve_fecha_fin=date.today() + timedelta(days=32),
        eve_estado="Pendiente",
        eve_capacidad=100,
        eve_tienecosto=True,
        eve_imagen=self.imagen_fake,
        eve_administrador_fk=self.administrador,
    )


    def test_cupos_maximos_y_costo(self):
        """Verifica que se puedan definir cupos y detalles de costo"""
        self.assertEqual(self.evento.eve_capacidad, 100)
        self.assertTrue(self.evento.eve_tienecosto)
        self.assertEqual(self.evento.eve_valor, 50000)
        self.assertEqual(self.evento.eve_metodo_pago, "Tarjeta")

    def test_validacion_fechas_limite(self):
        """Verifica que las fechas límite sean anteriores a la fecha de inicio"""
        self.assertLess(self.evento.eve_fecha_limite_inscripcion, self.evento.eve_fecha_inicio)
        self.assertLess(self.evento.eve_fecha_limite_revision, self.evento.eve_fecha_inicio)

    def test_requiere_evaluacion_activa_gestion_instrumento(self):
        """Si el evento requiere evaluación, se habilita HU74"""
        self.assertTrue(self.evento.eve_requiere_evaluacion)
        # Aquí podrías simular que la vista activa la opción de HU74
        # Ejemplo: check de flag o URL disponible
        # self.assertTrue(self.evento.hu74_habilitado)  # si tu modelo lo tiene
