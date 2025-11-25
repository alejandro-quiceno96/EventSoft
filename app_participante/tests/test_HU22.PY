from django.test import TestCase, Client
from django.urls import reverse

from app_usuarios.models import Usuario
class PerfilUsuarioTestCase(TestCase):
    """Pruebas automatizadas para la historia de usuario HU22: Visualización y edición del perfil."""

    def setUp(self):
        # Crear usuario base de prueba
        self.user = Usuario.objects.create_user(
            username='exponente1',
            password='test12345',
            first_name='Carlos',
            last_name='Pérez',
            email='carlos@example.com',
            telefono='3105555555',
            fecha_nacimiento='1998-05-20'
        )
        self.client = Client()
        self.url_ver_perfil = reverse('app_participante:ver_info_participante')
        self.url_editar_perfil = reverse('app_participante:editar_perfil')

    # --------------------------------------------------------
    # 1️⃣ Verificación de acceso
    # --------------------------------------------------------
    def test_usuario_no_autenticado_redirigido_al_login(self):
        """Si el usuario no está logueado, debe redirigirse al login."""
        response = self.client.get(self.url_ver_perfil)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_usuario_autenticado_puede_ver_perfil(self):
        """El usuario autenticado puede acceder a su perfil y ver sus datos."""
        self.client.login(username='exponente1', password='test12345')
        response = self.client.get(self.url_ver_perfil)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carlos')
        self.assertContains(response, 'Pérez')
        self.assertContains(response, 'carlos@example.com')
        self.assertContains(response, '3105555555')

    # --------------------------------------------------------
    # 2️⃣ Edición del perfil (sin cambiar contraseña)
    # --------------------------------------------------------
    def test_editar_datos_basicos(self):
        """El usuario puede actualizar su información básica."""
        self.client.login(username='exponente1', password='test12345')
        data = {
            'first_name': 'Juan',
            'last_name': 'Ramírez',
            'email': 'juan@example.com',
            'telefono': '3119998888',
            'username': 'exponente1'
        }
        response = self.client.post(self.url_editar_perfil, data, follow=True)

        self.user.refresh_from_db()
        self.assertRedirects(response, self.url_ver_perfil)
        self.assertEqual(self.user.first_name, 'Juan')
        self.assertEqual(self.user.last_name, 'Ramírez')
        self.assertEqual(self.user.email, 'juan@example.com')
        self.assertEqual(self.user.telefono, '3119998888')

    # --------------------------------------------------------
    # 3️⃣ Cambio de contraseña exitoso
    # --------------------------------------------------------
    def test_cambio_contrasena_exitoso(self):
        """El usuario puede cambiar su contraseña correctamente."""
        self.client.login(username='exponente1', password='test12345')
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'test12345',
            'new_password': 'nuevaClave123',
            'confirm_password': 'nuevaClave123',
        }
        response = self.client.post(self.url_editar_perfil, data, follow=True)
        self.assertRedirects(response, self.url_ver_perfil)

        # Verificar que la contraseña fue cambiada
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nuevaClave123'))

    # --------------------------------------------------------
    # 4️⃣ Error: contraseña actual incorrecta
    # --------------------------------------------------------
    def test_error_contrasena_actual_incorrecta(self):
        """Debe mostrar un mensaje de error si la contraseña actual es incorrecta."""
        self.client.login(username='exponente1', password='test12345')
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'incorrecta',
            'new_password': 'claveNueva123',
            'confirm_password': 'claveNueva123',
        }
        response = self.client.post(self.url_editar_perfil, data, follow=True)

        self.assertRedirects(response, self.url_ver_perfil)
        self.user.refresh_from_db()
        # La contraseña no debe haber cambiado
        self.assertTrue(self.user.check_password('test12345'))
