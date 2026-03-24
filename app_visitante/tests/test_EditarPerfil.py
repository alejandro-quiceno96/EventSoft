import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.db import IntegrityError

User = get_user_model()

class EditarPerfilTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario para testing
        self.usuario = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Juan',
            last_name='Pérez',
            segundo_nombre='Carlos',
            segundo_apellido='Gómez',
            telefono='123456789',
            fecha_nacimiento='1990-01-01',
            tipo_documento='CC',
            documento_identidad='123456789'
        )
        
        # URL para los tests
        self.url = reverse('editar_perfil')
        
        # Autenticar como el usuario
        self.client.login(username='testuser', password='password123')
        
        # Datos completos para actualización básica
        self.datos_completos = {
            'first_name': 'Juan Updated',
            'last_name': 'Pérez Updated',
            'username': 'testuser_updated',
            'email': 'updated@example.com',
            'segundo_nombre': 'Carlos Updated',
            'segundo_apellido': 'Gómez Updated',
            'telefono': '987654321',
            'fecha_nacimiento': '1995-05-15'
        }
        
        # Datos para cambio de contraseña
        self.datos_cambio_password = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'segundo_nombre': 'Carlos',
            'segundo_apellido': 'Gómez',
            'telefono': '123456789',
            'fecha_nacimiento': '1990-01-01',
            'current_password': 'password123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }
    
    def test_actualizacion_datos_basicos_exitosa(self):
        """CA1: Actualización exitosa de datos básicos del perfil"""
        response = self.client.post(self.url, self.datos_completos)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('inicio_vistante'))
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        
        # Verificar que los datos fueron actualizados
        self.assertEqual(usuario_actualizado.first_name, 'Juan Updated')
        self.assertEqual(usuario_actualizado.last_name, 'Pérez Updated')
        self.assertEqual(usuario_actualizado.username, 'testuser_updated')
        self.assertEqual(usuario_actualizado.email, 'updated@example.com')
        self.assertEqual(usuario_actualizado.segundo_nombre, 'Carlos Updated')
        self.assertEqual(usuario_actualizado.segundo_apellido, 'Gómez Updated')
        self.assertEqual(usuario_actualizado.telefono, '987654321')
        self.assertEqual(str(usuario_actualizado.fecha_nacimiento), '1995-05-15')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Perfil actualizado correctamente.')
    
    def test_actualizacion_campos_parciales(self):
        """CA1: Actualización exitosa con solo algunos campos (función mejorada)"""
        # Con la función mejorada, podemos enviar solo los campos que queremos cambiar
        datos_parciales = {
            'first_name': 'Solo Nombre Actualizado',
            'email': 'parcial@example.com'
            # No enviar otros campos - con la función mejorada mantendrán sus valores
        }
        
        response = self.client.post(self.url, datos_parciales)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        
        # Verificar campos actualizados
        self.assertEqual(usuario_actualizado.first_name, 'Solo Nombre Actualizado')
        self.assertEqual(usuario_actualizado.email, 'parcial@example.com')
        
        # Verificar campos no enviados mantienen sus valores originales
        self.assertEqual(usuario_actualizado.last_name, 'Pérez')
        self.assertEqual(usuario_actualizado.username, 'testuser')
        self.assertEqual(usuario_actualizado.segundo_nombre, 'Carlos')
        self.assertEqual(usuario_actualizado.segundo_apellido, 'Gómez')
        self.assertEqual(usuario_actualizado.telefono, '123456789')
        self.assertEqual(str(usuario_actualizado.fecha_nacimiento), '1990-01-01')
    
    def test_cambio_password_exitoso(self):
        """CA2: Cambio de contraseña exitoso con validación correcta"""
        self.assertTrue(self.usuario.check_password('password123'))
        
        response = self.client.post(self.url, self.datos_cambio_password)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        self.assertTrue(usuario_actualizado.check_password('newpassword456'))
        self.assertTrue('_auth_user_id' in self.client.session)
        
        messages = list(get_messages(response.wsgi_request))
        mensajes_texto = [str(msg) for msg in messages]
        self.assertIn('Contraseña actualizada correctamente.', mensajes_texto)
        self.assertIn('Perfil actualizado correctamente.', mensajes_texto)
    
    def test_cambio_password_actual_incorrecta(self):
        """CA2: Error al cambiar contraseña con contraseña actual incorrecta"""
        datos = self.datos_cambio_password.copy()
        datos['current_password'] = 'incorrecta'
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actual = User.objects.get(id=self.usuario.id)
        self.assertTrue(usuario_actual.check_password('password123'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'La contraseña actual es incorrecta.')
    
    def test_cambio_password_no_coinciden(self):
        """CA2: Error cuando las nuevas contraseñas no coinciden"""
        datos = self.datos_cambio_password.copy()
        datos['confirm_password'] = 'diferente'
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actual = User.objects.get(id=self.usuario.id)
        self.assertTrue(usuario_actual.check_password('password123'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Las contraseñas no coinciden o están vacías.')
    
    def test_cambio_password_corta(self):
        """CA2: Error cuando la nueva contraseña es muy corta"""
        datos = self.datos_cambio_password.copy()
        datos['new_password'] = '123'
        datos['confirm_password'] = '123'
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actual = User.objects.get(id=self.usuario.id)
        self.assertTrue(usuario_actual.check_password('password123'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'La contraseña debe tener al menos 8 caracteres.')
    
    def test_username_duplicado(self):
        """CA1: Error al usar username duplicado"""
        # Crear otro usuario
        User.objects.create_user(
            username='usuario_existente',
            email='existente@example.com',
            password='password123'
        )
        
        datos = self.datos_completos.copy()
        datos['username'] = 'usuario_existente'  # Username ya existente
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'El nombre de usuario ya está en uso.')
    
    def test_email_duplicado(self):
        """CA1: Error al usar email duplicado"""
        # Crear otro usuario
        User.objects.create_user(
            username='otro_usuario',
            email='duplicado@example.com',
            password='password123'
        )
        
        datos = self.datos_completos.copy()
        datos['email'] = 'duplicado@example.com'  # Email ya existente
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'El correo electrónico ya está en uso.')
    
    def test_fecha_nacimiento_invalida(self):
        """CA1: Error con formato de fecha inválido"""
        datos = self.datos_completos.copy()
        datos['fecha_nacimiento'] = 'formato-invalido'
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Formato de fecha inválido. Use YYYY-MM-DD.')
    
    def test_fecha_nacimiento_vacia(self):
        """CA1: Manejo correcto de fecha de nacimiento vacía"""
        datos = self.datos_completos.copy()
        datos['fecha_nacimiento'] = ''  # Fecha vacía
        
        response = self.client.post(self.url, datos)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        self.assertIsNone(usuario_actualizado.fecha_nacimiento)
    
    def test_metodo_get_redirige(self):
        """CA1: Método GET redirige sin actualizar perfil"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin:index_super_admin'))
        
        usuario_actual = User.objects.get(id=self.usuario.id)
        self.assertEqual(usuario_actual.first_name, 'Juan')
        self.assertEqual(usuario_actual.username, 'testuser')
    
    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        
        response = client_no_auth.post(self.url, self.datos_completos)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_sesion_mantiene_despues_cambio_password(self):
        """CA2: La sesión se mantiene activa después de cambiar contraseña"""
        self.assertTrue('_auth_user_id' in self.client.session)
        session_user_id_antes = self.client.session['_auth_user_id']
        
        response = self.client.post(self.url, self.datos_cambio_password)
        
        self.assertTrue('_auth_user_id' in self.client.session)
        session_user_id_despues = self.client.session['_auth_user_id']
        
        self.assertEqual(session_user_id_antes, session_user_id_despues)
        self.assertEqual(session_user_id_despues, str(self.usuario.id))
    
    def test_actualizacion_solo_telefono(self):
        """CA1: Actualización exitosa solo del teléfono"""
        datos_telefono = {
            'telefono': '999888777'
        }
        
        response = self.client.post(self.url, datos_telefono)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        self.assertEqual(usuario_actualizado.telefono, '999888777')
        self.assertEqual(usuario_actualizado.first_name, 'Juan')  # Sin cambios
        self.assertEqual(usuario_actualizado.email, 'testuser@example.com')  # Sin cambios
    
    def test_campos_vacios_manejo_correcto(self):
        """CA1: Manejo correcto de campos vacíos"""
        datos_vacios = {
            'first_name': '',
            'last_name': '',
            'segundo_nombre': '',
            'segundo_apellido': '',
            'telefono': ''
        }
        
        response = self.client.post(self.url, datos_vacios)
        
        self.assertEqual(response.status_code, 302)
        
        usuario_actualizado = User.objects.get(id=self.usuario.id)
        self.assertEqual(usuario_actualizado.first_name, '')
        self.assertEqual(usuario_actualizado.last_name, '')
        self.assertEqual(usuario_actualizado.segundo_nombre, '')
        self.assertEqual(usuario_actualizado.segundo_apellido, '')
        self.assertEqual(usuario_actualizado.telefono, '')
        # Campos no enviados mantienen sus valores
        self.assertEqual(usuario_actualizado.username, 'testuser')
        self.assertEqual(usuario_actualizado.email, 'testuser@example.com')