import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from app_usuarios.models import Usuario as User

class RecuperarContraseñaSessionTestCase(TestCase):
    """Tests para la vista de recuperación de contraseña usando sesiones"""
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.url = reverse('recuperar_contraseña')
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
    
    def test_acceso_pagina_recuperacion(self):
        """CA1: La página de recuperación carga correctamente (paso 1)"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/recuperar_con.html')
        
        # Verificar que empieza en paso 1
        context = response.context
        self.assertEqual(context['paso'], 1)
        self.assertFalse(context['mostrarmensajes'])
    
    @patch('app_visitante.views.send_mail')
    def test_paso_1_email_valido(self, mock_send_mail):
        """CA1: Paso 1 - Email válido envía código y guarda en sesión"""
        data = {
            'email': 'test@example.com'
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/recuperar_con.html')
        
        # Verificar que avanzó al paso 2
        context = response.context
        self.assertEqual(context['paso'], 2)
        self.assertEqual(context['email'], 'test@example.com')
        
        # Verificar que se guardó en sesión
        session_data = self.client.session.get('codigo_recuperacion')
        self.assertIsNotNone(session_data)
        self.assertEqual(session_data['email'], 'test@example.com')
        self.assertIn('codigo', session_data)
        self.assertIn('expira', session_data)
        
        # Verificar que se llamó a send_mail
        mock_send_mail.assert_called_once()
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Se envió un código a tu correo' in str(message) for message in messages))
    
    def test_paso_1_email_no_existe(self):
        """CA2: Paso 1 - Email no existe muestra error"""
        data = {
            'email': 'noexiste@example.com'
        }
        
        response = self.client.post(self.url, data)
        
        # Verificar que se queda en paso 1
        context = response.context
        self.assertEqual(context['paso'], 1)
        
        # Verificar que NO se guardó en sesión
        session_data = self.client.session.get('codigo_recuperacion')
        self.assertIsNone(session_data)
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('correo ingresado no está registrado' in str(message) for message in messages))
    
    
    @patch('app_visitante.views.send_mail')
    def test_flujo_completo_exitoso(self, mock_send_mail):
        """CA1: Flujo completo exitoso usando sesiones"""
        # Paso 1: Enviar email
        data_paso1 = {'email': 'test@example.com'}
        response1 = self.client.post(self.url, data_paso1)
        
        # Obtener código de la sesión
        session = self.client.session
        codigo = session['codigo_recuperacion']['codigo']
        email = session['codigo_recuperacion']['email']
        
        # Paso 2: Verificar código
        data_paso2 = {
            'email': email,
            'codigo': codigo
        }
        response2 = self.client.post(self.url, data_paso2)
        
        # Verificar que avanzó al paso 3
        self.assertEqual(response2.context['paso'], 3)
        
        # Verificar que se marcó como verificado en sesión
        session = self.client.session
        self.assertTrue(session.get('codigo_verificado', False))
        
        # Paso 3: Cambiar contraseña
        data_paso3 = {
            'email': email,
            'nueva_password': 'newpassword123',
            'confirmar_password': 'newpassword123'
        }
        response3 = self.client.post(self.url, data_paso3)
        
        # Verificar redirección a login
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(response3.url, reverse('login'))
        
        # Verificar que la contraseña fue cambiada
        user_actualizado = User.objects.get(email='test@example.com')
        self.assertTrue(user_actualizado.check_password('newpassword123'))
        
        # Verificar que se limpió la sesión
        session = self.client.session
        self.assertNotIn('codigo_recuperacion', session)
        self.assertNotIn('codigo_verificado', session)
    
    @patch('app_visitante.views.send_mail')
    def test_paso_2_codigo_incorrecto(self, mock_send_mail):
        """CA2: Paso 2 - Código incorrecto muestra error"""
        # Paso 1: Enviar email
        data_paso1 = {'email': 'test@example.com'}
        self.client.post(self.url, data_paso1)
        
        # Obtener código real de la sesión
        session = self.client.session
        codigo_real = session['codigo_recuperacion']['codigo']
        
        # Paso 2: Intentar con código incorrecto
        data_paso2 = {
            'email': 'test@example.com',
            'codigo': '000000'  # Código incorrecto
        }
        
        response = self.client.post(self.url, data_paso2)
        
        # Verificar que se queda en paso 2 con error
        context = response.context
        self.assertEqual(context['paso'], 2)
        
        # Verificar que NO se marcó como verificado
        session = self.client.session
        self.assertFalse(session.get('codigo_verificado', False))
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Código inválido o expirado' in str(message) for message in messages))
    
    @patch('app_visitante.views.send_mail')
    def test_paso_2_sin_codigo_en_sesion(self, mock_send_mail):
        """CA2: Paso 2 - Sin código en sesión (acceso directo)"""
        # Acceder directamente al paso 2 sin haber hecho paso 1
        data_paso2 = {
            'email': 'test@example.com',
            'codigo': '123456'
        }
        
        response = self.client.post(self.url, data_paso2)
        
        # Debería volver al paso 1 o mostrar error
        context = response.context
        self.assertIn(context['paso'], [1, 2])
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
    
    @patch('app_visitante.views.send_mail')
    def test_paso_3_contraseñas_no_coinciden(self, mock_send_mail):
        """CA3: Paso 3 - Contraseñas no coinciden muestra error"""
        # Simular flujo completo hasta paso 3
        # Paso 1: Enviar email
        data_paso1 = {'email': 'test@example.com'}
        self.client.post(self.url, data_paso1)
        
        # Paso 2: Verificar código
        session = self.client.session
        data_paso2 = {
            'email': 'test@example.com',
            'codigo': session['codigo_recuperacion']['codigo']
        }
        self.client.post(self.url, data_paso2)
        
        # Paso 3: Intentar cambiar con contraseñas diferentes
        data_paso3 = {
            'email': 'test@example.com',
            'nueva_password': 'newpassword123',
            'confirmar_password': 'diferente123'
        }
        
        response = self.client.post(self.url, data_paso3)
        
        # Verificar que se queda en paso 3
        context = response.context
        self.assertEqual(context['paso'], 3)
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Las contraseñas no coinciden' in str(message) for message in messages))
    
    @patch('app_visitante.views.send_mail')
    def test_paso_3_sin_verificacion_previo(self, mock_send_mail):
        """CA3: Paso 3 - Sin verificación previa del código"""
        # Acceder directamente al paso 3 sin verificar código
        data_paso3 = {
            'email': 'test@example.com',
            'nueva_password': 'newpassword123',
            'confirmar_password': 'newpassword123'
        }
        
        response = self.client.post(self.url, data_paso3)
        
        # Debería redirigir o mostrar error
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            context = response.context
            self.assertIn(context['paso'], [1, 2, 3])
        
        # La contraseña NO debería cambiar
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user.check_password('oldpassword123'))
