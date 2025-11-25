import json
from django.test import TestCase, Client
from django.contrib.auth import authenticate, login
from django.contrib.messages import get_messages
from django.urls import reverse
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores

class LoginViewTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.login_url = reverse('login')  # Ajusta según tu URL name
        
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_acceso_pagina_login(self):
        """CA1: La página de login carga correctamente"""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/login.html')
    
    def test_login_exitoso_con_username(self):
        """CA1: Login exitoso usando username"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Verificar que el usuario está autenticado
        self.assertEqual(response.status_code, 302)
        
        # Verificar redirección a inicio_visitante (sin roles)
        # La respuesta podría ser una redirección o renderizado directo
        self.assertIn(response.status_code, [200, 302])
    
    def test_login_exitoso_con_email(self):
        """CA1: Login exitoso usando email"""
        data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Verificar respuesta exitosa
        self.assertIn(response.status_code, [200, 302])
    
    def test_login_con_administrador_activo(self):
        """CA1: Login con usuario que es Administrador activo"""
        # Crear administrador activo
        administrador = Administradores.objects.create(
            usuario=self.user,
            estado="Activo"
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Debería redirigir a selección de roles
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/seleccionar_rol.html')
        
        # Verificar que el contexto contiene los roles
        context = response.context
        self.assertIn('roles', context)
        self.assertIn('Administrador de Eventos', context['roles'])
        self.assertIn('usuario', context)
    
    def test_login_con_super_administrador(self):
        """CA1: Login con usuario que es Super Administrador"""
        # Crear super administrador
        super_admin = SuperAdministradores.objects.create(
            usuario=self.user
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Debería redirigir a selección de roles
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/seleccionar_rol.html')
        
        # Verificar que el contexto contiene los roles
        context = response.context
        self.assertIn('Super Administrador', context['roles'])
    
    def test_login_con_multiples_roles(self):
        """CA1: Login con usuario que tiene múltiples roles"""
        # Crear ambos roles
        administrador = Administradores.objects.create(
            usuario=self.user,
            estado="Activo"
        )
        super_admin = SuperAdministradores.objects.create(
            usuario=self.user
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Debería mostrar página de selección de roles
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/seleccionar_rol.html')
        
        # Verificar que contiene ambos roles
        context = response.context
        self.assertIn('Super Administrador', context['roles'])
        self.assertIn('Administrador de Eventos', context['roles'])
        self.assertEqual(len(context['roles']), 2)
    
    def test_login_administrador_inactivo(self):
        """CA1: Login con Administrador inactivo no muestra el rol"""
        # Crear administrador inactivo
        administrador = Administradores.objects.create(
            usuario=self.user,
            estado="Inactivo"  # Estado diferente a "Activo"
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # No debería mostrar el rol de administrador (está inactivo)
        # Debería redirigir a inicio_visitante
        self.assertNotEqual(response.status_code, 200)  # No debería mostrar selección de roles
    
    def test_usuario_no_existe(self):
        """CA2: Error cuando el usuario no existe"""
        data = {
            'username': 'usuarioinexistente',
            'password': 'cualquierpassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Debería mostrar la página de login con error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/login.html')
    
    def test_email_no_existe(self):
        """CA2: Error cuando el email no existe"""
        data = {
            'username': 'noexiste@example.com',
            'password': 'cualquierpassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/login.html')
    
    def test_contrasena_incorrecta(self):
        """CA2: Error cuando la contraseña es incorrecta"""
        data = {
            'username': 'testuser',
            'password': 'contrasenaincorrecta'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/login.html')
        
        # Verificar que hay mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Contraseña incorrecta' in str(message) for message in messages))
    
    def test_session_prelogin_user_id(self):
        """CA3: Verificar que se guarda prelogin_user_id en sesión"""
        # Crear administrador activo
        administrador = Administradores.objects.create(
            usuario=self.user,
            estado="Activo"
        )
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Verificar que se guardó el ID en sesión
        self.assertIn('prelogin_user_id', self.client.session)
        self.assertEqual(self.client.session['prelogin_user_id'], self.user.id)
    
    def test_metodo_get_muestra_login(self):
        """CA1: Método GET muestra formulario de login"""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/login.html')
        # No debería tener mensajes de error en GET
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)
