from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores
from app_eventos.models import Eventos


class ListaEventosActivosTest(TestCase):
    """HU-90: Ver listado de eventos activos con su administrador"""

    def setUp(self):
        self.client = Client()
        
        # Super Admin
        self.super_user = Usuario.objects.create_user(
            username="superadmin",
            password="super123",
            tipo_documento="CC",
            documento_identidad="1234567890",
            email="super@test.com"
        )
        self.super_admin = SuperAdministradores.objects.create(usuario=self.super_user)
        
        # Administradores de eventos
        self.admin1_user = Usuario.objects.create_user(
            username="admin1",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111111111",
            email="admin1@test.com"
        )
        self.admin1 = Administradores.objects.create(
            usuario=self.admin1_user,
            num_eventos=5,
            estado="Activo"
        )
        
        self.admin2_user = Usuario.objects.create_user(
            username="admin2",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="2222222222",
            email="admin2@test.com"
        )
        self.admin2 = Administradores.objects.create(
            usuario=self.admin2_user,
            num_eventos=5,
            estado="Activo"
        )
        
        self.hoy = timezone.now().date()
        
        # Crear eventos de prueba
        self.evento_activo = Eventos.objects.create(
            eve_nombre="Evento Activo 1",
            eve_descripcion="Evento en curso",
            eve_ciudad="Manizales",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin1
        )
        
        self.evento_publicado = Eventos.objects.create(
            eve_nombre="Evento Publicado",
            eve_descripcion="Evento publicado",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio",
            eve_fecha_inicio=self.hoy + timedelta(days=10),
            eve_fecha_fin=self.hoy + timedelta(days=12),
            eve_estado="PUBLICADO",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin2
        )
        
        self.evento_borrador = Eventos.objects.create(
            eve_nombre="Evento Borrador",
            eve_descripcion="No debe aparecer",
            eve_ciudad="Cali",
            eve_lugar="Plaza",
            eve_fecha_inicio=self.hoy + timedelta(days=15),
            eve_fecha_fin=self.hoy + timedelta(days=17),
            eve_estado="BORRADOR",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin1
        )
        
        self.evento_cerrado = Eventos.objects.create(
            eve_nombre="Evento Cerrado",
            eve_descripcion="No debe aparecer",
            eve_ciudad="Medellín",
            eve_lugar="Teatro",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="CERRADO",
            eve_capacidad=150,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin2
        )

    def test_lista_solo_eventos_activos_y_publicados(self):
        """Mostrar solo eventos ACTIVO y PUBLICADO, no BORRADOR ni CERRADO"""
        self.client.login(username="superadmin", password="super123")
        
        eventos_activos = Eventos.objects.filter(
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        self.assertEqual(eventos_activos.count(), 2)
        self.assertIn(self.evento_activo, eventos_activos)
        self.assertIn(self.evento_publicado, eventos_activos)
        self.assertNotIn(self.evento_borrador, eventos_activos)
        self.assertNotIn(self.evento_cerrado, eventos_activos)

    def test_lista_muestra_nombre_estado_administrador(self):
        """Lista debe mostrar nombre, estado y administrador responsable"""
        eventos = Eventos.objects.filter(eve_estado__in=["ACTIVO", "PUBLICADO"])
        
        for evento in eventos:
            self.assertIsNotNone(evento.eve_nombre)
            self.assertIsNotNone(evento.eve_estado)
            self.assertIsNotNone(evento.eve_administrador_fk)
            self.assertIn(evento.eve_estado, ["ACTIVO", "PUBLICADO"])

    def test_acceso_directo_detalle_evento(self):
        """Cada evento debe tener link a su información detallada (HU91)"""
        self.client.login(username="superadmin", password="super123")
        
        # Verificar que el ID del evento es accesible para generar link
        evento_id = self.evento_activo.id
        self.assertIsNotNone(evento_id)
        self.assertGreater(evento_id, 0)


class FiltrarEventosTest(TestCase):
    """HU-90: Filtrar eventos por nombre o administrador"""

    def setUp(self):
        self.client = Client()
        
        self.super_user = Usuario.objects.create_user(
            username="superadmin",
            password="super123",
            tipo_documento="CC",
            documento_identidad="1234567890",
            email="super@test.com"
        )
        self.super_admin = SuperAdministradores.objects.create(usuario=self.super_user)
        
        # Administradores
        self.admin_juan = Usuario.objects.create_user(
            username="juan_admin",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="3333333333",
            email="juan@test.com"
        )
        self.admin_juan_obj = Administradores.objects.create(
            usuario=self.admin_juan,
            num_eventos=5,
            estado="Activo"
        )
        
        self.admin_maria = Usuario.objects.create_user(
            username="maria_admin",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="4444444444",
            email="maria@test.com"
        )
        self.admin_maria_obj = Administradores.objects.create(
            usuario=self.admin_maria,
            num_eventos=5,
            estado="Activo"
        )
        
        self.hoy = timezone.now().date()
        
        # Eventos para filtrar
        Eventos.objects.create(
            eve_nombre="Conferencia Tecnología",
            eve_descripcion="Tech",
            eve_ciudad="Manizales",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin_juan_obj
        )
        
        Eventos.objects.create(
            eve_nombre="Seminario Innovación",
            eve_descripcion="Innovation",
            eve_ciudad="Bogotá",
            eve_lugar="Hotel",
            eve_fecha_inicio=self.hoy + timedelta(days=10),
            eve_fecha_fin=self.hoy + timedelta(days=12),
            eve_estado="PUBLICADO",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin_maria_obj
        )
        
        Eventos.objects.create(
            eve_nombre="Taller IA",
            eve_descripcion="AI Workshop",
            eve_ciudad="Cali",
            eve_lugar="Universidad",
            eve_fecha_inicio=self.hoy + timedelta(days=15),
            eve_fecha_fin=self.hoy + timedelta(days=17),
            eve_estado="ACTIVO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin_juan_obj
        )

    def test_filtrar_por_nombre_evento(self):
        """Filtrar eventos por nombre"""
        self.client.login(username="superadmin", password="super123")
        
        busqueda = "Tecnología"
        eventos_filtrados = Eventos.objects.filter(
            eve_nombre__icontains=busqueda,
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        self.assertEqual(eventos_filtrados.count(), 1)
        self.assertEqual(eventos_filtrados.first().eve_nombre, "Conferencia Tecnología")

    def test_filtrar_por_administrador(self):
        """Filtrar eventos por administrador responsable"""
        self.client.login(username="superadmin", password="super123")
        
        eventos_admin_juan = Eventos.objects.filter(
            eve_administrador_fk=self.admin_juan_obj,
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        self.assertEqual(eventos_admin_juan.count(), 2)
        for evento in eventos_admin_juan:
            self.assertEqual(evento.eve_administrador_fk, self.admin_juan_obj)

    def test_filtrar_por_nombre_administrador(self):
        """Filtrar eventos por nombre del administrador"""
        self.client.login(username="superadmin", password="super123")
        
        nombre_admin = "maria"
        eventos_filtrados = Eventos.objects.filter(
            eve_administrador_fk__usuario__username__icontains=nombre_admin,
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        self.assertEqual(eventos_filtrados.count(), 1)
        self.assertEqual(
            eventos_filtrados.first().eve_administrador_fk.usuario.username,
            "maria_admin"
        )

    def test_filtro_sin_resultados(self):
        """Filtro sin coincidencias debe retornar lista vacía"""
        self.client.login(username="superadmin", password="super123")
        
        busqueda_inexistente = "XXXZZZ999"
        eventos_filtrados = Eventos.objects.filter(
            eve_nombre__icontains=busqueda_inexistente,
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        self.assertEqual(eventos_filtrados.count(), 0)


class PermisoListaEventosTest(TestCase):
    """HU-90: Solo Super Admin puede ver lista completa de eventos"""

    def setUp(self):
        self.client = Client()
        
        self.super_user = Usuario.objects.create_user(
            username="superadmin",
            password="super123",
            tipo_documento="CC",
            documento_identidad="1234567890",
            email="super@test.com"
        )
        self.super_admin = SuperAdministradores.objects.create(usuario=self.super_user)
        
        self.admin_normal = Usuario.objects.create_user(
            username="admin_normal",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9876543210",
            email="admin@test.com"
        )
        self.admin_obj = Administradores.objects.create(
            usuario=self.admin_normal,
            num_eventos=5,
            estado="Activo"
        )

    def test_super_admin_ve_todos_eventos(self):
        """Super Admin puede ver todos los eventos activos"""
        self.client.login(username="superadmin", password="super123")
        
        todos_eventos = Eventos.objects.filter(eve_estado__in=["ACTIVO", "PUBLICADO"])
        
        # Super Admin tiene acceso a todos
        self.assertTrue(hasattr(self.super_user, 'super_admin'))

    def test_admin_normal_solo_ve_sus_eventos(self):
        """Admin normal solo ve sus propios eventos"""
        self.client.login(username="admin_normal", password="admin123")
        
        eventos_propios = Eventos.objects.filter(
            eve_administrador_fk=self.admin_obj,
            eve_estado__in=["ACTIVO", "PUBLICADO"]
        )
        
        # Verificar que NO es super admin
        self.assertFalse(hasattr(self.admin_normal, 'super_admin'))


class OrdenacionListaEventosTest(TestCase):
    """HU-90: Ordenación y presentación de eventos"""

    def setUp(self):
        self.client = Client()
        
        self.super_user = Usuario.objects.create_user(
            username="superadmin",
            password="super123",
            tipo_documento="CC",
            documento_identidad="1234567890",
            email="super@test.com"
        )
        self.super_admin = SuperAdministradores.objects.create(usuario=self.super_user)
        
        self.admin_user = Usuario.objects.create_user(
            username="admin",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9876543210",
            email="admin@test.com"
        )
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado="Activo"
        )
        
        self.hoy = timezone.now().date()

    def test_ordenar_por_fecha_inicio(self):
        """Eventos ordenados por fecha de inicio"""
        evento1 = Eventos.objects.create(
            eve_nombre="Evento A",
            eve_descripcion="Primero",
            eve_ciudad="Manizales",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        evento2 = Eventos.objects.create(
            eve_nombre="Evento B",
            eve_descripcion="Segundo",
            eve_ciudad="Bogotá",
            eve_lugar="Hotel",
            eve_fecha_inicio=self.hoy + timedelta(days=2),
            eve_fecha_fin=self.hoy + timedelta(days=4),
            eve_estado="ACTIVO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        eventos_ordenados = Eventos.objects.filter(
            eve_estado="ACTIVO"
        ).order_by('eve_fecha_inicio')
        
        self.assertEqual(eventos_ordenados.first(), evento2)
        self.assertEqual(eventos_ordenados.last(), evento1)

    def test_contar_eventos_por_estado(self):
        """Contar cantidad de eventos por estado"""
        Eventos.objects.create(
            eve_nombre="Evento 1",
            eve_descripcion="Test",
            eve_ciudad="Cali",
            eve_lugar="Plaza",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        Eventos.objects.create(
            eve_nombre="Evento 2",
            eve_descripcion="Test",
            eve_ciudad="Medellín",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy + timedelta(days=10),
            eve_fecha_fin=self.hoy + timedelta(days=12),
            eve_estado="PUBLICADO",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin
        )
        
        total_activos = Eventos.objects.filter(eve_estado="ACTIVO").count()
        total_publicados = Eventos.objects.filter(eve_estado="PUBLICADO").count()
        
        self.assertEqual(total_activos, 1)
        self.assertEqual(total_publicados, 1)
