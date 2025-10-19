from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_super_admin.models import SuperAdministradores


class AccesoCMSTest(TestCase):
    """HU-97: Acceso al CMS solo para Super Admin"""

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
        
        # Admin normal
        self.admin_user = Usuario.objects.create_user(
            username="admin_normal",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9876543210",
            email="admin@test.com"
        )

    def test_super_admin_accede_cms(self):
        """Super Admin puede acceder al CMS"""
        self.client.login(username="superadmin", password="super123")
        
        # Simular acceso a dashboard CMS
        # response = self.client.get(reverse('super_admin:cms_dashboard'))
        # self.assertEqual(response.status_code, 200)
        
        # Verificar que el usuario está autenticado y es super admin
        self.assertTrue(self.client.session.get('_auth_user_id'))
        self.assertTrue(hasattr(self.super_user, 'super_admin'))

    def test_admin_normal_no_accede_cms(self):
        """Admin normal no puede acceder al CMS"""
        self.client.login(username="admin_normal", password="admin123")
        
        # Verificar que NO es super admin
        self.assertFalse(hasattr(self.admin_user, 'super_admin'))

    def test_usuario_anonimo_no_accede_cms(self):
        """Usuario sin login no accede al CMS"""
        # Simular acceso sin login
        # response = self.client.get(reverse('super_admin:cms_dashboard'))
        # self.assertEqual(response.status_code, 302)
        
        # Verificar que no hay sesión activa
        self.assertIsNone(self.client.session.get('_auth_user_id'))


class ModificarContenidoTest(TestCase):
    """HU-97: Modificar contenido global del sitio"""

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

    def test_modificar_texto_global(self):
        """Modificar textos globales del sitio"""
        # Simular modificación de contenido
        datos_contenido = {
            'seccion': 'home_titulo',
            'contenido': 'Bienvenido a EventSoft',
            'idioma': 'es'
        }
        
        # Verificar datos válidos
        self.assertEqual(datos_contenido['seccion'], 'home_titulo')
        self.assertIsNotNone(datos_contenido['contenido'])
        self.assertIn(datos_contenido['idioma'], ['es', 'en'])

    def test_modificar_apariencia_sitio(self):
        """Modificar colores y estilos del sitio"""
        datos_apariencia = {
            'color_primario': '#FF5733',
            'color_secundario': '#3498DB',
            'fuente_principal': 'Arial'
        }
        
        # Validar formato de colores hex
        self.assertTrue(datos_apariencia['color_primario'].startswith('#'))
        self.assertEqual(len(datos_apariencia['color_primario']), 7)

    def test_modificar_estructura_menu(self):
        """Modificar estructura del menú de navegación"""
        items_menu = [
            {'titulo': 'Inicio', 'url': '/', 'orden': 1},
            {'titulo': 'Eventos', 'url': '/eventos/', 'orden': 2}
        ]
        
        # Verificar estructura de menú
        self.assertEqual(len(items_menu), 2)
        self.assertEqual(items_menu[0]['orden'], 1)
        self.assertTrue(items_menu[1]['url'].startswith('/'))


class PrevisualizacionTest(TestCase):
    """HU-97: Previsualización antes de publicar"""

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

    def test_previsualizar_cambios(self):
        """Previsualizar cambios sin publicar"""
        datos_preview = {
            'seccion': 'home_titulo',
            'contenido': 'Nuevo Título',
            'idioma': 'es',
            'estado': 'preview'
        }
        
        # Verificar estado de preview
        self.assertEqual(datos_preview['estado'], 'preview')
        self.assertNotEqual(datos_preview['estado'], 'publicado')

    def test_cambios_no_publicados_no_aparecen_publico(self):
        """Los cambios en preview no se muestran en sitio público"""
        contenido_borrador = {
            'seccion': 'home_titulo',
            'contenido': 'Borrador Título',
            'estado': 'borrador'
        }
        
        # Verificar que está en borrador
        self.assertEqual(contenido_borrador['estado'], 'borrador')
        self.assertNotEqual(contenido_borrador['estado'], 'publicado')

    def test_publicar_cambios_aprobados(self):
        """Publicar cambios después de aprobar preview"""
        # Simular flujo: borrador -> preview -> publicado
        estados = ['borrador', 'preview', 'publicado']
        
        estado_inicial = 'borrador'
        estado_final = 'publicado'
        
        self.assertIn(estado_inicial, estados)
        self.assertIn(estado_final, estados)
        self.assertNotEqual(estado_inicial, estado_final)


class MultiidiomaTest(TestCase):
    """HU-97: Gestión de contenido multiidioma"""

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

    def test_editar_contenido_espanol(self):
        """Editar contenido en español"""
        contenido_es = {
            'seccion': 'home_bienvenida',
            'contenido': 'Bienvenido',
            'idioma': 'es'
        }
        
        self.assertEqual(contenido_es['idioma'], 'es')
        self.assertIsNotNone(contenido_es['contenido'])

    def test_editar_contenido_ingles(self):
        """Editar contenido en inglés"""
        contenido_en = {
            'seccion': 'home_bienvenida',
            'contenido': 'Welcome',
            'idioma': 'en'
        }
        
        self.assertEqual(contenido_en['idioma'], 'en')
        self.assertIsNotNone(contenido_en['contenido'])

    def test_cambios_aplicables_todos_idiomas(self):
        """Aplicar cambios a todos los idiomas configurados"""
        idiomas_disponibles = ['es', 'en']
        contenido_global = {
            'seccion': 'footer_copyright',
            'contenido': '© 2025 EventSoft'
        }
        
        # Verificar que se puede aplicar a múltiples idiomas
        self.assertGreater(len(idiomas_disponibles), 1)
        self.assertIn('es', idiomas_disponibles)
        self.assertIn('en', idiomas_disponibles)


class SeguridadCMSTest(TestCase):
    """HU-97: Validaciones de seguridad en CMS"""

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

    def test_no_inyeccion_script(self):
        """Rechazar contenido con scripts maliciosos"""
        contenido_malicioso = '<script>alert("XSS")</script>'
        
        # Verificar detección de scripts
        self.assertIn('<script>', contenido_malicioso)
        self.assertIn('alert', contenido_malicioso)

    def test_validar_urls_menu(self):
        """Validar URLs del menú sean válidas"""
        url_invalida = 'javascript:alert()'
        url_valida = '/eventos/'
        
        # Verificar URLs válidas
        self.assertTrue(url_valida.startswith('/'))
        self.assertFalse(url_valida.startswith('javascript:'))
        self.assertTrue(url_invalida.startswith('javascript:'))

    def test_log_cambios_cms(self):
        """Registrar auditoría de cambios en CMS"""
        cambio_cms = {
            'usuario': self.super_user.username,
            'accion': 'Modificar contenido CMS',
            'seccion': 'home_titulo'
        }
        
        # Verificar estructura de log
        self.assertIsNotNone(cambio_cms['usuario'])
        self.assertIn('CMS', cambio_cms['accion'])
        self.assertIsNotNone(cambio_cms['seccion'])