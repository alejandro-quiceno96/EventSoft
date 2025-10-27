from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from app_eventos.models import Eventos, EventosCategorias
from app_administrador.models import Administradores
from app_categorias.models import Categorias
from app_areas.models import Areas
from django.core.files.uploadedfile import SimpleUploadedFile

Usuario = get_user_model()


class EventoTests(TestCase):
    def setUp(self):
        self.imagen_fake = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        # Crear usuario
        self.user = Usuario.objects.create_user(
            username="admin",
            password="12345",
            email="admin@test.com"
        )

        # Crear administrador
        self.administrador = Administradores.objects.create(
            usuario=self.user,
        )

        # Crear área y categoría
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
            eve_nombre="Congreso de Innovación 2025",
            eve_descripcion="Evento sobre innovación tecnológica",
            eve_ciudad="Manizales",
            eve_lugar="Auditorio Principal",
            eve_fecha_inicio=date(2025, 12, 10),
            eve_fecha_fin=date(2025, 12, 12),
            eve_estado="Pendiente",
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen=self.imagen_fake,  # 🔹 agregar la imagen
        )

        # Evento futuro
        self.evento_futuro = Eventos.objects.create(
            eve_nombre="Congreso de Innovación 2025",
            eve_descripcion="Evento sobre innovación tecnológica",
            eve_ciudad="Manizales",
            eve_lugar="Auditorio Principal",
            eve_fecha_inicio=date.today() + timedelta(days=30),
            eve_fecha_fin=date.today() + timedelta(days=32),
            eve_estado="Pendiente",
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen=self.imagen_fake,  # 🔹 agregar la imagen
        )

        # Evento pasado
        self.evento_pasado = Eventos.objects.create(
            eve_nombre="Feria Académica 2020",
            eve_descripcion="Evento pasado",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio 2",
            eve_fecha_inicio=date.today() - timedelta(days=100),
            eve_fecha_fin=date.today() - timedelta(days=99),
            eve_estado="Finalizado",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen=self.imagen_fake,  # 🔹 agregar la imagen
        )
        # Relación evento ↔ categoría
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_futuro,
            eve_cat_categoria_fk=self.categoria
        )

    def test_evento_se_crea_correctamente(self):
        """Verifica que el evento se creó con los datos correctos"""
        self.assertEqual(self.evento_futuro.eve_nombre, "Congreso de Innovación 2025")
        self.assertEqual(self.evento_futuro.eve_ciudad, "Manizales")
        self.assertEqual(self.evento_futuro.eve_estado, "Pendiente")

    def test_crear_evento_view_post(self):
        """Prueba la creación de un evento vía POST"""
        self.client.login(username="admin", password="12345")

        response = self.client.post(reverse("administrador:crear_evento"), {
            "nombre_evento": "Simposio de Robótica",
            "descripcion_evento": "Evento de robótica temprana",
            "ciudad": "Bogotá",
            "lugar": "Centro de Convenciones",
            "fecha_inicio": "2025-11-20",
            "fecha_fin": "2025-11-22",
            "categoria": self.categoria.id,
            "inscripcion": "No",
            "permitir_participantes": "1",
            "cantidad_personas": 150,
        })

        self.assertEqual(response.status_code, 302)  # redirección tras crear
        self.assertTrue(Eventos.objects.filter(eve_nombre="Simposio de Robótica").exists())

    def test_listado_eventos_futuros(self):
        """La interfaz debe mostrar solo eventos futuros"""
        self.client.login(username="admin", password="12345")
        # 🔹 Asegúrate de tener esta URL en tu urls.py
        response = self.client.get(reverse("administrador:evento_detalle", args=[self.evento.id]))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["eve_nombre"], "Congreso de Innovación 2025")

        self.assertNotContains(response, "Feria Académica 2020")

    def test_detalle_evento_url_unica(self):
        """Al seleccionar un evento se debe mostrar detalle con URL única"""
        response = self.client.get(reverse("administrador:evento_detalle", args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["eve_nombre"], "Congreso de Innovación 2025")

    def test_filtro_por_ciudad(self):
        """El buscador debe filtrar eventos por ciudad"""
        self.client.login(username="admin", password="12345")
        # 🔹 Asegúrate de tener esta URL en tu urls.py
        response = self.client.get(reverse("administrador:index_administrador") + "?ciudad=Manizales")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Congreso de Innovación 2025")
