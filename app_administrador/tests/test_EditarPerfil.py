import json
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from app_administrador.models import Administradores  # Ajusta según tu app

User = get_user_model()

class EditarPerfilTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario de prueba con todos los campos
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Juan',
            last_name='Perez',
            segundo_nombre='Carlos',
            segundo_apellido='Gomez',
            tipo_documento='CC',
            documento_identidad='123456789',
            fecha_nacimiento=date(1990, 1, 1),
            telefono='3001234567'
        )
        
        # Crear administrador asociado si es necesario
        self.administrador = Administradores.objects.create(
            usuario=self.user,
        )
        
        self.url = reverse('administrador:editar_perfil')
        self.client.login(username='testuser', password='testpass123')
    
    def test_acceso_sin_autenticar(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_actualizacion_campos_basicos(self):
        """CA1: Actualización correcta de campos básicos del usuario"""
        data = {
            'first_name': 'Pedro',
            'last_name': 'Rodriguez',
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'segundo_nombre': 'Andres',
            'segundo_apellido': 'Lopez',
            'telefono': '3109876543',
            'fecha_nacimiento': '1995-05-15'
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrador:index_administrador'))
        
        # Verificar que el usuario fue actualizado en la base de datos
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertEqual(user_actualizado.first_name, 'Pedro')
        self.assertEqual(user_actualizado.last_name, 'Rodriguez')
        self.assertEqual(user_actualizado.username, 'nuevousuario')
        self.assertEqual(user_actualizado.email, 'nuevo@example.com')
        self.assertEqual(user_actualizado.segundo_nombre, 'Andres')
        self.assertEqual(user_actualizado.segundo_apellido, 'Lopez')
        self.assertEqual(user_actualizado.telefono, '3109876543')
        self.assertEqual(str(user_actualizado.fecha_nacimiento), '1995-05-15')
    
    def test_actualizacion_campos_vacios(self):
        """CA1: Manejo correcto de campos vacíos"""
        data = {
            'first_name': '',
            'last_name': '',
            'username': 'usuariovacio',
            'email': '',
            'segundo_nombre': '',
            'segundo_apellido': '',
            'telefono': '',
            'fecha_nacimiento': ''
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que los campos se guardaron como vacíos
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertEqual(user_actualizado.first_name, '')
        self.assertEqual(user_actualizado.last_name, '')
        self.assertEqual(user_actualizado.segundo_nombre, '')
        self.assertEqual(user_actualizado.segundo_apellido, '')
        self.assertEqual(user_actualizado.telefono, '')
        self.assertIsNone(user_actualizado.fecha_nacimiento)
    
    def test_cambio_contrasena_exitoso(self):
        """CA2: Cambio de contraseña exitoso con datos válidos"""
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'testpass123',  # Contraseña actual correcta
            'new_password': 'nuevapass123',
            'confirm_password': 'nuevapass123'
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la contraseña fue cambiada
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertTrue(user_actualizado.check_password('nuevapass123'))
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Contraseña actualizada correctamente' in str(message) for message in messages))
    
    def test_cambio_contrasena_actual_incorrecta(self):
        """CA2: Error cuando la contraseña actual es incorrecta"""
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'contrasenaincorrecta',  # Contraseña actual incorrecta
            'new_password': 'nuevapass123',
            'confirm_password': 'nuevapass123'
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la contraseña NO fue cambiada
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertTrue(user_actualizado.check_password('testpass123'))  # Sigue siendo la original
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('La contraseña actual es incorrecta' in str(message) for message in messages))
    
    def test_cambio_contrasena_no_coinciden(self):
        """CA2: Error cuando las nuevas contraseñas no coinciden"""
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'testpass123',
            'new_password': 'nuevapass123',
            'confirm_password': 'diferentecontrasena'  # No coincide
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la contraseña NO fue cambiada
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertTrue(user_actualizado.check_password('testpass123'))
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Las contraseñas no coinciden' in str(message) for message in messages))
    
    def test_cambio_contrasena_vacia(self):
        """CA2: Error cuando la nueva contraseña está vacía"""
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'testpass123',
            'new_password': '',  # Contraseña vacía
            'confirm_password': ''  # Confirmación vacía
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la contraseña NO fue cambiada
        user_actualizado = User.objects.get(id=self.user.id)
        self.assertTrue(user_actualizado.check_password('testpass123'))
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Las contraseñas no coinciden o están vacías' in str(message) for message in messages))
    
    def test_mensaje_exito_actualizacion_perfil(self):
        """CA3: Mensaje de éxito al actualizar perfil sin cambiar contraseña"""
        data = {
            'first_name': 'NuevoNombre',
            'last_name': 'NuevoApellido',
            'username': self.user.username,
            'email': self.user.email,
            # Sin campos de contraseña
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Perfil actualizado correctamente' in str(message) for message in messages))
    
    def test_metodo_get_redirige(self):
        """CA3: Método GET redirige a index_administrador"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrador:index_administrador'))
    
    def test_sesion_mantiene_despues_cambio_contrasena(self):
        """CA2: La sesión se mantiene activa después de cambiar contraseña"""
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email,
            'current_password': 'testpass123',
            'new_password': 'nuevapass123',
            'confirm_password': 'nuevapass123'
        }
        
        # Verificar que está logueado antes del cambio
        response_before = self.client.get(reverse('administrador:index_administrador'))
        self.assertEqual(response_before.status_code, 200)
        
        # Cambiar contraseña
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que sigue logueado después del cambio
        response_after = self.client.get(reverse('administrador:index_administrador'))
        self.assertEqual(response_after.status_code, 200)
