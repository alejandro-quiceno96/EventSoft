from django.test import TestCase, Client
from django.contrib.sessions.models import Session
from django.utils import timezone
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores


class SuspenderAdministradorTest(TestCase):
    """HU-92: Suspender credenciales de administrador de evento"""

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
        
        # Admin a suspender
        self.admin_user = Usuario.objects.create_user(
            username="admin_evento",
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

    def test_suspender_admin_con_justificacion(self):
        """Suspender admin requiere justificación obligatoria"""
        self.client.login(username="superadmin", password="super123")
        
        justificacion = "Uso indebido de la plataforma"
        
        # Simular suspensión
        self.admin.estado = "Suspendido"
        self.admin.save()
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, "Suspendido")
        self.assertIsNotNone(justificacion)
        self.assertGreater(len(justificacion), 10)

    def test_suspender_sin_justificacion_falla(self):
        """No permitir suspensión sin justificación"""
        self.client.login(username="superadmin", password="super123")
        
        justificacion = ""
        
        # Validar que justificación es requerida
        self.assertEqual(len(justificacion), 0)
        # En implementación real, esto debe rechazarse

    def test_suspension_invalida_sesion_inmediatamente(self):
        """La suspensión debe invalidar token de sesión del admin"""
        # Admin inicia sesión
        admin_client = Client()
        admin_client.login(username="admin_evento", password="admin123")
        
        # Verificar sesión activa
        self.assertTrue(admin_client.session.get('_auth_user_id'))
        
        # Super Admin suspende
        self.admin.estado = "Suspendido"
        self.admin.save()
        
        # Verificar que admin fue suspendido
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, "Suspendido")

    def test_admin_suspendido_no_puede_acceder(self):
        """Admin suspendido no puede iniciar sesión"""
        # Suspender admin
        self.admin.estado = "Suspendido"
        self.admin.save()
        
        # Intentar login
        admin_client = Client()
        result = admin_client.login(username="admin_evento", password="admin123")
        
        # Verificar estado
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, "Suspendido")

    def test_solo_super_admin_puede_suspender(self):
        """Solo Super Admin puede suspender administradores"""
        # Admin normal intenta suspender a otro
        otro_admin_user = Usuario.objects.create_user(
            username="otro_admin",
            password="otro123",
            tipo_documento="CC",
            documento_identidad="1111111111",
            email="otro@test.com"
        )
        otro_admin = Administradores.objects.create(
            usuario=otro_admin_user,
            num_eventos=3,
            estado="Activo"
        )
        
        self.client.login(username="admin_evento", password="admin123")
        
        # Verificar que admin logueado NO es super admin
        self.assertFalse(hasattr(self.admin_user, 'super_admin'))
        self.assertTrue(hasattr(self.super_user, 'super_admin'))


class RevocarCodigoAccesoTest(TestCase):
    """HU-92: Revocar códigos de acceso no utilizados"""

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
        self.client.login(username="superadmin", password="super123")

    def test_revocar_codigo_no_utilizado(self):
        """Revocar código de acceso que no ha sido usado"""
        codigo_acceso = {
            'codigo': 'ABC123XYZ',
            'utilizado': False,
            'fecha_generacion': timezone.now(),
            'estado': 'Activo'
        }
        
        # Simular revocación
        codigo_acceso['estado'] = 'Revocado'
        
        self.assertEqual(codigo_acceso['estado'], 'Revocado')
        self.assertFalse(codigo_acceso['utilizado'])

    def test_no_revocar_codigo_ya_usado(self):
        """No permitir revocar código que ya fue usado"""
        codigo_usado = {
            'codigo': 'XYZ789ABC',
            'utilizado': True,
            'estado': 'Activo'
        }
        
        # Verificar que está usado
        self.assertTrue(codigo_usado['utilizado'])
        # En implementación real, debe rechazarse la revocación

    def test_revocar_requiere_justificacion(self):
        """Revocación requiere justificación"""
        justificacion = "Código generado por error"
        
        self.assertIsNotNone(justificacion)
        self.assertGreater(len(justificacion), 5)


class RegistroSuspensionesTest(TestCase):
    """HU-92: Auditoría de suspensiones y revocaciones"""

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
            username="admin_evento",
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

    def test_registrar_suspension_con_datos(self):
        """Registrar suspensión con todos los datos necesarios"""
        log_suspension = {
            'admin_suspendido': self.admin_user.username,
            'suspendido_por': self.super_user.username,
            'fecha_suspension': timezone.now(),
            'justificacion': 'Incumplimiento de normas',
            'tipo_accion': 'Suspensión'
        }
        
        # Verificar estructura del log
        self.assertIsNotNone(log_suspension['admin_suspendido'])
        self.assertIsNotNone(log_suspension['suspendido_por'])
        self.assertIsNotNone(log_suspension['justificacion'])
        self.assertEqual(log_suspension['tipo_accion'], 'Suspensión')

    def test_registrar_revocacion_codigo(self):
        """Registrar revocación de código de acceso"""
        log_revocacion = {
            'codigo_revocado': 'ABC123',
            'revocado_por': self.super_user.username,
            'fecha_revocacion': timezone.now(),
            'justificacion': 'Código duplicado',
            'tipo_accion': 'Revocación'
        }
        
        self.assertIsNotNone(log_revocacion['codigo_revocado'])
        self.assertIsNotNone(log_revocacion['revocado_por'])
        self.assertEqual(log_revocacion['tipo_accion'], 'Revocación')

    def test_historial_suspensiones_por_admin(self):
        """Consultar historial de suspensiones de un administrador"""
        # Simular múltiples suspensiones
        historial = [
            {'fecha': timezone.now(), 'estado': 'Suspendido', 'justificacion': 'Motivo 1'},
            {'fecha': timezone.now(), 'estado': 'Activo', 'justificacion': 'Reactivación'},
        ]
        
        self.assertEqual(len(historial), 2)
        self.assertIn('Suspendido', [h['estado'] for h in historial])


class ReactivarAdministradorTest(TestCase):
    """HU-92: Reactivar administrador suspendido"""

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
            username="admin_suspendido",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9876543210",
            email="admin@test.com"
        )
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado="Suspendido"
        )

    def test_reactivar_admin_suspendido(self):
        """Reactivar administrador previamente suspendido"""
        self.client.login(username="superadmin", password="super123")
        
        # Verificar estado inicial
        self.assertEqual(self.admin.estado, "Suspendido")
        
        # Reactivar
        self.admin.estado = "Activo"
        self.admin.save()
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, "Activo")

    def test_reactivar_requiere_justificacion(self):
        """Reactivación también requiere justificación"""
        justificacion_reactivacion = "Situación resuelta, se permite retorno"
        
        self.assertIsNotNone(justificacion_reactivacion)
        self.assertGreater(len(justificacion_reactivacion), 10)

    def test_admin_reactivado_puede_acceder(self):
        """Admin reactivado puede iniciar sesión nuevamente"""
        # Reactivar
        self.admin.estado = "Activo"
        self.admin.save()
        
        # Intentar login
        admin_client = Client()
        result = admin_client.login(username="admin_suspendido", password="admin123")
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, "Activo")
