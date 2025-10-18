from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores


class HU90_VerEventosActivosSuperAdminTest(TestCase):
    """HU-90: Ver listado de eventos activos con su respectivo administrador"""

    def setUp(self):
        """Configuración inicial de los objetos para las pruebas"""
        # Crear usuario SuperAdmin
        self.super_admin = Usuario.objects.create_user(
            username="superadmin",
            password="12345",
            tipo_documento="CC",
            documento_identidad="123456789",
            email="superadmin@test.com",
            tipo_usuario="SUPERADMIN"
        )

        # Crear usuarios administradores
        self.user_admin1 = Usuario.objects.create_user(
            username="admin1",
            password="12345",
            tipo_documento="CC",
            documento_identidad="11111111",
            email="admin1@test.com",
            tipo_usuario="ADMIN"
        )
        self.user_admin2 = Usuario.objects.create_user(
            username="admin2",
            password="12345",
            tipo_documento="CC",
            documento_identidad="22222222",
            email="admin2@test.com",
            tipo_usuario="ADMIN"
        )

        # Crear administradores asociados
        self.admin1 = Administradores.objects.create(usuario=self.user_admin1, estado="Activo")
        self.admin2 = Administradores.objects.create(usuario=self.user_admin2, estado="Activo")

        # Crear eventos con diferentes estados
        self.evento_activo_1 = Eventos.objects.create(
            eve_nombre="Evento Activo 1",
            eve_descripcion="Evento en ejecución",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio Principal",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=1),
            eve_fecha_fin=timezone.now().date() + timedelta(days=2),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin1
        )

        self.evento_activo_2 = Eventos.objects.create(
            eve_nombre="Evento Activo 2",
            eve_descripcion="Otro evento activo",
            eve_ciudad="Medellín",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=3),
            eve_fecha_fin=timezone.now().date() + timedelta(days=4),
            eve_estado="ACTIVO",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin2
        )

        self.evento_borrador = Eventos.objects.create(
            eve_nombre="Evento Borrador",
            eve_descripcion="Evento aún no publicado",
            eve_ciudad="Cali",
            eve_lugar="Salón 3",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="BORRADOR",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin1
        )

        # Iniciar sesión como SuperAdmin
        self.client.login(username="superadmin", password="12345")

    # ---------------------------------------------
    # TEST 1: Ver listado general
    # ---------------------------------------------
    def test_superadmin_ve_solo_eventos_activos(self):
        """
        CA1: El Super Admin debe ver únicamente eventos con estado ACTIVO
        """
        response = self.client.get(reverse("super_admin:lista_eventos"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Verificar que aparecen los eventos activos
        self.assertIn("Evento Activo 1", content)
        self.assertIn("Evento Activo 2", content)

        # Verificar que NO aparece el borrador
        self.assertNotIn("Evento Borrador", content)

    # ---------------------------------------------
    # TEST 2: Filtrado por nombre del evento
    # ---------------------------------------------
    def test_filtrado_por_nombre_evento(self):
        """
        CA2: La lista debe permitir filtrar por nombre de evento
        """
        response = self.client.get(reverse("super_admin:lista_eventos") + "?nombre=Evento Activo 1")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Solo debe aparecer el evento filtrado
        self.assertIn("Evento Activo 1", content)
        self.assertNotIn("Evento Activo 2", content)

    # ---------------------------------------------
    # TEST 3: Filtrado por administrador
    # ---------------------------------------------
    def test_filtrado_por_administrador(self):
        """
        CA3: La lista debe permitir filtrar por el administrador del evento
        """
        response = self.client.get(reverse("super_admin:lista_eventos") + f"?administrador={self.admin2.id}")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Solo deben aparecer eventos del admin filtrado
        self.assertIn("Evento Activo 2", content)
        self.assertNotIn("Evento Activo 1", content)

    # ---------------------------------------------
    # TEST 4: Verificar columnas requeridas
    # ---------------------------------------------
    def test_tabla_muestra_columnas_necesarias(self):
        """
        CA4: La tabla debe mostrar nombre del evento, estado y administrador
        """
        response = self.client.get(reverse("super_admin:lista_eventos"))
        content = response.content.decode()

        self.assertIn("Evento Activo 1", content)
        self.assertIn("ACTIVO", content)
        self.assertIn(self.admin1.usuario.username, content)

    # ---------------------------------------------
    # TEST 5: Link a detalle del evento (HU91)
    # ---------------------------------------------
    def test_tiene_link_a_detalle_evento(self):
        """
        CA5: Cada evento debe tener link a la vista de detalle (HU91)
        """
        response = self.client.get(reverse("super_admin:lista_eventos"))
        content = response.content.decode()

        # Verificar que el link contiene la ruta esperada (ejemplo)
        detalle_url = reverse("super_admin:detalle_evento", args=[self.evento_activo_1.id])
        self.assertIn(detalle_url, content)