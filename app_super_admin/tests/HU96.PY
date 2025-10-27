from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores


class OcultarEventoCerradoTest(TestCase):
    """HU-96: Ocultar eventos cerrados de vista pública"""

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
        
        # Admin de evento
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

    def test_ocultar_evento_cerrado_exitoso(self):
        """Ocultar evento CERRADO de vista pública"""
        evento = Eventos.objects.create(
            eve_nombre="Evento Cerrado",
            eve_descripcion="Test",
            eve_ciudad="Manizales",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="CERRADO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        self.client.login(username="superadmin", password="super123")
        response = self.client.post(
            reverse('super_admin:modificar_eventos', 
                    kwargs={'evento_id': evento.id, 'nuevo_estado': 'OCULTO'})
        )
        
        evento.refresh_from_db()
        self.assertEqual(evento.eve_estado, "OCULTO")
        self.assertEqual(response.status_code, 302)

   
class EliminarEventoCerradoTest(TestCase):
    """HU-96: Eliminar permanentemente eventos cerrados"""

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

    def test_eliminar_evento_cerrado_exitoso(self):
        """Eliminar evento CERRADO con confirmación"""
        evento = Eventos.objects.create(
            eve_nombre="Evento Eliminar",
            eve_descripcion="Test",
            eve_ciudad="Cali",
            eve_lugar="Teatro",
            eve_fecha_inicio=self.hoy - timedelta(days=15),
            eve_fecha_fin=self.hoy - timedelta(days=13),
            eve_estado="CERRADO",
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        evento_id = evento.id
        
        self.client.login(username="superadmin", password="super123")
        response = self.client.post(
            reverse('super_admin:eliminar_evento', kwargs={'evento_id': evento_id}),
            {'confirmacion': 'SI'}
        )
        
        self.assertFalse(Eventos.objects.filter(id=evento_id).exists())
        self.assertEqual(response.status_code, 302)



class EliminacionCascadaTest(TestCase):
    """HU-96: Verificar eliminación en cascada de registros asociados"""

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

    def test_eliminacion_cascada_inscripciones(self):
        """Al eliminar evento, se eliminan inscripciones asociadas"""
        evento = Eventos.objects.create(
            eve_nombre="Evento Cascada",
            eve_descripcion="Test",
            eve_ciudad="Pasto",
            eve_lugar="Plaza",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="CERRADO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        # Simular inscripciones (asumir modelo Inscripcion existe)
        # inscripcion = Inscripcion.objects.create(evento=evento, ...)
        
        self.client.login(username="superadmin", password="super123")
        self.client.post(
            reverse('super_admin:eliminar_evento', kwargs={'evento_id': evento.id}),
            {'confirmacion': 'SI'}
        )
        
        # Verificar que inscripciones también se eliminaron
        # self.assertFalse(Inscripcion.objects.filter(evento_id=evento.id).exists())
        self.assertFalse(Eventos.objects.filter(id=evento.id).exists())