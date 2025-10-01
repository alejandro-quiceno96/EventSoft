from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos, EventosCategorias
from app_categorias.models import Categorias
from app_areas.models import Areas
from app_administrador.models import Administradores
from app_usuarios.models import Usuario


class BusquedaEventosTest(TestCase):
    def setUp(self):
        # Crear usuario y administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            password="12345",
            tipo_documento="CC",
            documento_identidad="123456789",
            email="admin@test.com"
        )
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=3,
            estado="Activo"
        )

        # Crear áreas y categorías
        self.area1 = Areas.objects.create(
            are_nombre="Tecnología", are_descripcion="Área de tecnología"
        )
        self.area2 = Areas.objects.create(
            are_nombre="Salud", are_descripcion="Área de salud"
        )

        self.categoria1 = Categorias.objects.create(
            cat_nombre="Conferencia",
            cat_descripcion="Charlas y conferencias",
            cat_area_fk=self.area1
        )
        self.categoria2 = Categorias.objects.create(
            cat_nombre="Taller",
            cat_descripcion="Talleres prácticos",
            cat_area_fk=self.area2
        )

        # Crear eventos futuros
        self.evento1 = Eventos.objects.create(
            eve_nombre="Evento Tecnología",
            eve_descripcion="Evento relacionado con tecnología",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio A",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="activo",
            eve_imagen="image/evento1.png",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk_id=self.admin.id
        )
        self.evento2 = Eventos.objects.create(
            eve_nombre="Evento Salud",
            eve_descripcion="Evento relacionado con salud",
            eve_ciudad="Medellín",
            eve_lugar="Auditorio B",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=10),
            eve_fecha_fin=timezone.now().date() + timedelta(days=11),
            eve_estado="activo",
            eve_imagen="image/evento2.png",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk_id=self.admin.id
        )

        # Relacionar eventos con categorías
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento1,
            eve_cat_categoria_fk=self.categoria1
        )
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento2,
            eve_cat_categoria_fk=self.categoria2
        )

    def test_filtrar_por_categoria(self):
        """Debe filtrar eventos por categoría"""
        response = self.client.get(reverse('inicio_visitante'), {"categoria": self.categoria1.id})
        contenido = response.content.decode()
        self.assertIn(self.evento1.eve_nombre, contenido)
        self.assertNotIn(self.evento2.eve_nombre, contenido)

    def test_filtrar_por_area(self):
        """Debe filtrar eventos por área"""
        response = self.client.get(reverse('inicio_visitante'), {"area": self.area2.id})
        contenido = response.content.decode()
        self.assertIn(self.evento2.eve_nombre, contenido)
        self.assertNotIn(self.evento1.eve_nombre, contenido)

    def test_filtrar_por_fecha_inicio(self):
        """Debe filtrar eventos por fecha de inicio"""
        fecha = str(self.evento1.eve_fecha_inicio)
        response = self.client.get(reverse('inicio_visitante'), {"fecha_inicio": fecha})
        contenido = response.content.decode()
        self.assertIn(self.evento1.eve_nombre, contenido)
        self.assertNotIn(self.evento2.eve_nombre, contenido)


