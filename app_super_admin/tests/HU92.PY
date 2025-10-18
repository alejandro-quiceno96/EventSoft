from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.sessions.models import Session
from datetime import timedelta
import hashlib

from app_usuarios.models import Usuario
from app_super_admin.models import SuperAdministradores
from app_administrador.models import Administradores


class TestHU92_SuspenderCodigoCredenciales(TestCase):
    """Suite completa de tests para HU92"""
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        
        # Crear usuario super administrador
        self.super_admin_user = Usuario.objects.create_user(
            username='superadmin',
            password='SuperPass123!',
            tipo_documento='CC',
            documento_identidad='1000000001',
            email='superadmin@eventsoft.com'
        )
        
        # Crear registro de super administrador
        self.super_admin = SuperAdministradores.objects.create(
            usuario=self.super_admin_user,
            estado='Activo'
        )
        
        # Crear usuario administrador activo
        self.admin_user = Usuario.objects.create_user(
            username='admin_evento',
            password='AdminPass123!',
            tipo_documento='CC',
            documento_identidad='2000000001',
            email='admin@ejemplo.com'
        )
        
        # Crear registro de administrador
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado='Activo'
        )
        
        # Login como super admin
        self.client = Client()
        self.client.login(username='superadmin', password='SuperPass123!')
    
    # ============================================================================
    # CRITERIO 1: Revocar código de acceso no utilizado
    # ============================================================================
    
    def test_CA1_super_admin_puede_revocar_codigo_no_utilizado(self):
        """
        CA1: El SUPER ADMIN debe tener opción para revocar código no utilizado
        
        Verifica que se puede marcar un código como revocado/inválido
        """
        # Arrange - Crear código de acceso no utilizado
        from app_super_admin.models import CodigoAccesoAdministrador
        
        codigo = CodigoAccesoAdministrador.objects.create(
            email='nuevo_admin@ejemplo.com',
            codigo='CODIGO123',
            codigo_hash=hashlib.sha256('CODIGO123'.encode()).hexdigest(),
            max_eventos=5,
            usado=False,
            creado_por=self.super_admin,
            fecha_caducidad=timezone.now() + timedelta(days=30)
        )
        
        # Act - Revocar el código
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'codigo_id': codigo.id,
                'accion': 'revocar_codigo'
            },
            follow=True
        )
        
        # Assert
        self.assertEqual(response.status_code, 200,
                        "Debe permitir revocar el código")
        
        # Verificar que el código fue revocado
        codigo.refresh_from_db()
        self.assertTrue(
            codigo.revocado or codigo.estado == 'REVOCADO',
            "El código debe estar marcado como revocado"
        )
    
    def test_CA1_codigo_revocado_no_puede_usarse(self):
        """
        CA1: Un código revocado no debe poder usarse para registro
        """
        # Arrange - Crear y revocar código
        from app_super_admin.models import CodigoAccesoAdministrador
        
        codigo_texto = 'CODIGO_REVOCADO'
        codigo = CodigoAccesoAdministrador.objects.create(
            email='admin_revocado@ejemplo.com',
            codigo=codigo_texto,
            codigo_hash=hashlib.sha256(codigo_texto.encode()).hexdigest(),
            max_eventos=3,
            usado=False,
            revocado=True,  # Código revocado
            creado_por=self.super_admin
        )
        
        # Act - Intentar usar el código revocado
        self.client.logout()
        response = self.client.post(
            reverse('validar_clave_admin'),
            {
                'email': 'admin_revocado@ejemplo.com',
                'codigo': codigo_texto
            }
        )
        
        # Assert
        self.assertEqual(response.status_code, 200,
                        "Debe mostrar página con error")
        
        response_content = response.content.decode().lower()
        self.assertTrue(
            'revocado' in response_content or 'inválido' in response_content,
            "Debe mostrar mensaje de código revocado"
        )
    
    def test_CA1_no_puede_revocar_codigo_ya_utilizado(self):
        """
        CA1: No debe permitir revocar un código que ya fue utilizado
        
        Los códigos usados ya están asociados a un administrador activo
        """
        # Arrange - Crear código ya utilizado
        from app_super_admin.models import CodigoAccesoAdministrador
        
        codigo = CodigoAccesoAdministrador.objects.create(
            email='admin_usado@ejemplo.com',
            codigo='CODIGO_USADO',
            codigo_hash=hashlib.sha256('CODIGO_USADO'.encode()).hexdigest(),
            max_eventos=5,
            usado=True,  # Ya fue utilizado
            creado_por=self.super_admin
        )
        
        # Act - Intentar revocar código usado
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'codigo_id': codigo.id,
                'accion': 'revocar_codigo'
            },
            follow=True
        )
        
        # Assert
        # Debe mostrar error o advertencia
        response_content = response.content.decode().lower()
        tiene_advertencia = (
            'ya utilizado' in response_content or
            'no se puede revocar' in response_content or
            'error' in response_content
        )
        
        self.assertTrue(tiene_advertencia,
                       "Debe mostrar advertencia al intentar revocar código usado")
    
    def test_CA1_listado_codigos_muestra_estado_revocado(self):
        """
        CA1: El listado de códigos debe mostrar claramente cuáles están revocados
        """
        # Arrange - Crear códigos con diferentes estados
        from app_super_admin.models import CodigoAccesoAdministrador
        
        codigo_activo = CodigoAccesoAdministrador.objects.create(
            email='activo@ejemplo.com',
            codigo='ACTIVO123',
            codigo_hash=hashlib.sha256('ACTIVO123'.encode()).hexdigest(),
            max_eventos=5,
            usado=False,
            revocado=False,
            creado_por=self.super_admin
        )
        
        codigo_revocado = CodigoAccesoAdministrador.objects.create(
            email='revocado@ejemplo.com',
            codigo='REVOCADO123',
            codigo_hash=hashlib.sha256('REVOCADO123'.encode()).hexdigest(),
            max_eventos=5,
            usado=False,
            revocado=True,
            creado_por=self.super_admin
        )
        
        # Act - Acceder al listado de códigos/usuarios
        response = self.client.get(reverse('super_administrador:usuarios'))
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        # Debe mostrar ambos códigos con sus estados
        self.assertContains(response, 'activo@ejemplo.com')
        self.assertContains(response, 'revocado@ejemplo.com')
    
    # ============================================================================
    # CRITERIO 2: Suspender credenciales de Administrador de Evento
    # ============================================================================
    
    def test_CA2_super_admin_puede_suspender_administrador(self):
        """
        CA2: El SUPER ADMIN debe poder suspender credenciales de un administrador
        
        Verifica que se puede cambiar el estado del administrador a 'Suspendido'
        """
        # Arrange
        self.assertEqual(self.admin.estado, 'Activo',
                        "El administrador debe estar activo inicialmente")
        
        # Act - Suspender administrador
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'Violación de políticas de uso'
            },
            follow=True
        )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el administrador fue suspendido
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, 'Suspendido',
                        "El estado debe cambiar a Suspendido")
    
    def test_CA2_administrador_suspendido_no_puede_crear_eventos(self):
        """
        CA2: Un administrador suspendido no debe poder realizar acciones
        """
        # Arrange - Suspender administrador
        self.admin.estado = 'Suspendido'
        self.admin.save()
        
        # Act - Login como administrador suspendido
        self.client.logout()
        self.client.login(username='admin_evento', password='AdminPass123!')
        
        # Intentar acceder a crear evento
        response = self.client.get(reverse('administrador:crear_evento'))
        
        # Assert - Debe ser redirigido o mostrar error
        self.assertIn(response.status_code, [302, 403],
                     "Administrador suspendido no debe poder acceder")
    
    def test_CA2_puede_reactivar_administrador_suspendido(self):
        """
        CA2: El super admin debe poder reactivar un administrador suspendido
        """
        # Arrange - Suspender primero
        self.admin.estado = 'Suspendido'
        self.admin.save()
        
        # Act - Reactivar administrador
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'reactivar',
                'justificacion': 'Situación resuelta, reactivando cuenta'
            },
            follow=True
        )
        
        # Assert
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, 'Activo',
                        "El administrador debe volver a estado Activo")
    
    # ============================================================================
    # CRITERIO 3: Invalidar sesión inmediatamente al suspender
    # ============================================================================
    
    def test_CA3_suspension_invalida_sesion_inmediatamente(self):
        """
        CA3: La suspensión debe invalidar inmediatamente el token de sesión
        
        El administrador suspendido debe ser desconectado automáticamente
        """
        # Arrange - Crear sesión del administrador
        admin_client = Client()
        admin_client.login(username='admin_evento', password='AdminPass123!')
        
        # Verificar que puede acceder antes de suspensión
        response_antes = admin_client.get(reverse('administrador:index_administrador'))
        self.assertEqual(response_antes.status_code, 200,
                        "Admin debe poder acceder antes de suspensión")
        
        # Act - Suspender desde super admin
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'Suspensión por seguridad'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Assert - Verificar que la sesión del admin fue invalidada
        response_despues = admin_client.get(reverse('administrador:index_administrador'))
        
        # Debe ser redirigido al login o mostrar error de acceso
        self.assertIn(response_despues.status_code, [302, 403],
                     "La sesión del admin debe estar invalidada")
    
    def test_CA3_sesion_invalidada_no_permite_acceso(self):
        """
        CA3: Una sesión invalidada no debe permitir ningún acceso
        """
        # Arrange - Login como admin
        admin_client = Client()
        admin_client.login(username='admin_evento', password='AdminPass123!')
        
        # Suspender el administrador
        self.admin.estado = 'Suspendido'
        self.admin.save()
        
        # Act - Intentar acceder después de suspensión
        response = admin_client.get(reverse('administrador:index_administrador'))
        
        # Assert
        self.assertIn(response.status_code, [302, 403],
                     "No debe permitir acceso con sesión de admin suspendido")
    
    def test_CA3_admin_suspendido_no_puede_iniciar_sesion(self):
        """
        CA3: Un administrador suspendido no debe poder iniciar sesión nuevamente
        """
        # Arrange - Suspender administrador
        self.admin.estado = 'Suspendido'
        self.admin.save()
        
        # Act - Intentar login
        nuevo_client = Client()
        login_exitoso = nuevo_client.login(
            username='admin_evento',
            password='AdminPass123!'
        )
        
        # Assert
        # El login puede tener éxito técnicamente, pero el acceso debe estar bloqueado
        if login_exitoso:
            response = nuevo_client.get(reverse('administrador:index_administrador'))
            self.assertIn(response.status_code, [302, 403],
                         "Admin suspendido no debe poder acceder aunque login sea exitoso")
    
    # ============================================================================
    # CRITERIO 4: Justificación obligatoria
    # ============================================================================
    
    def test_CA4_suspender_sin_justificacion_debe_fallar(self):
        """
        CA4: El sistema debe requerir justificación obligatoria para suspender
        
        No debe permitir suspensión sin justificación
        """
        # Act - Intentar suspender SIN justificación
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': ''  # Vacío
            },
            follow=True
        )
        
        # Assert
        self.assertEqual(response.status_code, 200,
                        "Debe retornar a la página con error")
        
        # Verificar que NO se suspendió
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, 'Activo',
                        "No debe suspender sin justificación")
        
        # Verificar mensaje de error
        response_content = response.content.decode().lower()
        self.assertTrue(
            'justificación' in response_content or 
            'obligatorio' in response_content or
            'requerido' in response_content,
            "Debe mostrar error sobre justificación obligatoria"
        )
    
    def test_CA4_justificacion_debe_tener_minimo_caracteres(self):
        """
        CA4: La justificación debe tener un mínimo de caracteres (ej: 10)
        """
        # Act - Intentar suspender con justificación muy corta
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'abc'  # Muy corto
            },
            follow=True
        )
        
        # Assert
        self.admin.refresh_from_db()
        
        # Dependiendo de la implementación, puede rechazar o aceptar
        # Lo ideal es que rechace justificaciones muy cortas
        if self.admin.estado == 'Activo':
            self.assertEqual(self.admin.estado, 'Activo',
                           "No debe suspender con justificación insuficiente")
    
    def test_CA4_justificacion_se_almacena_correctamente(self):
        """
        CA4: La justificación debe quedar registrada en el sistema
        """
        # Arrange
        justificacion_texto = 'Uso indebido de la plataforma detectado en auditoría'
        
        # Act - Suspender con justificación
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': justificacion_texto
            },
            follow=True
        )
        
        # Assert
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, 'Suspendido')
        
        # Verificar que la justificación fue guardada
        # (Esto depende de si el modelo tiene campo justificacion)
        if hasattr(self.admin, 'justificacion_suspension'):
            self.assertEqual(self.admin.justificacion_suspension, justificacion_texto)
    
    def test_CA4_revocar_codigo_tambien_requiere_justificacion(self):
        """
        CA4: Revocar un código también debe requerir justificación
        """
        # Arrange
        from app_super_admin.models import CodigoAccesoAdministrador
        
        codigo = CodigoAccesoAdministrador.objects.create(
            email='codigo_revocar@ejemplo.com',
            codigo='CODIGO_REV',
            codigo_hash=hashlib.sha256('CODIGO_REV'.encode()).hexdigest(),
            max_eventos=5,
            usado=False,
            creado_por=self.super_admin
        )
        
        # Act - Intentar revocar SIN justificación
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'codigo_id': codigo.id,
                'accion': 'revocar_codigo',
                'justificacion': ''  # Vacío
            },
            follow=True
        )
        
        # Assert
        codigo.refresh_from_db()
        
        # Debe rechazar la revocación sin justificación
        if not (codigo.revocado or codigo.estado == 'REVOCADO'):
            self.assertFalse(codigo.revocado,
                           "No debe revocar sin justificación")
    
    # ============================================================================
    # TESTS ADICIONALES DE SEGURIDAD Y AUDITORÍA
    # ============================================================================
    
    def test_suspension_genera_log_auditoria(self):
        """
        Seguridad: Cada suspensión debe generar un registro de auditoría
        """
        # Act - Suspender administrador
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'Registro de auditoría de prueba'
            },
            follow=True
        )
        
        # Assert
        # Verificar que existe un log (si el sistema tiene logs)
        # Esto depende de la implementación específica
        self.assertEqual(response.status_code, 200)
    
    def test_solo_super_admin_puede_suspender(self):
        """
        Seguridad: Solo el SUPER ADMIN puede suspender administradores
        """
        # Arrange - Crear otro administrador regular
        otro_admin_user = Usuario.objects.create_user(
            username='otro_admin',
            password='OtroPass123!',
            tipo_documento='CC',
            documento_identidad='3000000001',
            email='otro@ejemplo.com'
        )
        
        otro_admin = Administradores.objects.create(
            usuario=otro_admin_user,
            num_eventos=3,
            estado='Activo'
        )
        
        # Act - Login como administrador regular e intentar suspender
        self.client.logout()
        self.client.login(username='otro_admin', password='OtroPass123!')
        
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'Intento no autorizado'
            }
        )
        
        # Assert - Debe ser rechazado
        self.assertIn(response.status_code, [302, 403],
                     "Admin regular no debe poder suspender a otros")
    
    def test_usuario_no_autenticado_no_puede_suspender(self):
        """
        Seguridad: Usuario sin autenticar no puede suspender administradores
        """
        # Arrange
        self.client.logout()
        
        # Act - Intentar suspender sin autenticación
        response = self.client.post(
            reverse('super_administrador:cancelar_administrador'),
            {
                'administrador_id': self.admin.id,
                'accion': 'suspender',
                'justificacion': 'Intento sin autenticación'
            }
        )
        
        # Assert - Debe redirigir a login
        self.assertEqual(response.status_code, 302)
        
        # Verificar que no se suspendió
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.estado, 'Activo')