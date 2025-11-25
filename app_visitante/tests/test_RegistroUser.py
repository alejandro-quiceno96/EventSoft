import json
from django.test import TestCase, Client
from django.contrib.messages import get_messages
from django.urls import reverse
from django.db import IntegrityError
from unittest.mock import patch, MagicMock
from app_visitante.forms import RegistroUsuarioForm
from app_usuarios.models import Usuario as User

class RegistroUsuarioViewTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.url = reverse('registro')  # Ajusta según tu URL name
        
        # Datos de prueba para registro válido
        self.datos_validos = {
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'tipo_documento': 'CC',
            'documento_identidad': '123456789',
            'fecha_nacimiento': '1990-01-01',
            'telefono': '3001234567'
        }
    
    def test_acceso_pagina_registro(self):
        """CA1: La página de registro carga correctamente"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro.html')
        
        # Verificar que el formulario está en el contexto
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], RegistroUsuarioForm)
    
    @patch('app_visitante.views.RegistroUsuarioForm')
    def test_registro_exitoso(self, mock_form_class):
        """CA1: Registro exitoso con datos válidos"""
        # Mock del formulario válido
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = User(username='nuevousuario')
        mock_form_class.return_value = mock_form
        
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar redirección a login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        
        # Verificar que se llamó a save()
        mock_form.save.assert_called_once()
        
        # Verificar mensaje de éxito
        # Los mensajes se pueden verificar siguiendo la redirección
        response_follow = self.client.get(response.url, follow=True)
        messages = list(get_messages(response_follow.wsgi_request))
        self.assertTrue(any('Cuenta creada exitosamente' in str(message) for message in messages))
    
    @patch('app_visitante.views.RegistroUsuarioForm')
    def test_formulario_invalido(self, mock_form_class):
        """CA2: Formulario inválido muestra errores"""
        # Mock del formulario inválido
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form
        
        datos_invalidos = {
            'username': '',  # Campo requerido vacío
            'email': 'email-invalido',  # Email inválido
            'password1': 'pass',
            'password2': 'different'  # Contraseñas no coinciden
        }
        
        response = self.client.post(self.url, datos_invalidos)
        
        # Verificar que se muestra el formulario con errores
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro.html')
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Corrige los errores en el formulario' in str(message) for message in messages))
    
    @patch('app_visitante.views.RegistroUsuarioForm')
    def test_usuario_duplicado(self, mock_form_class):
        """CA3: Manejo de error de usuario duplicado"""
        # Mock del formulario que lanza IntegrityError
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.side_effect = IntegrityError('Usuario duplicado')
        mock_form_class.return_value = mock_form
        
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar que se muestra el formulario con error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro.html')
        
        # Verificar mensaje de error específico
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Ya existe un usuario con este documento' in str(message) for message in messages))
    
    @patch('app_visitante.views.RegistroUsuarioForm')
    def test_error_generico(self, mock_form_class):
        """CA3: Manejo de error genérico"""
        # Mock del formulario que lanza una excepción genérica
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.side_effect = Exception('Error de base de datos')
        mock_form_class.return_value = mock_form
        
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar que se muestra el formulario con error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro.html')
        
        # Verificar mensaje de error genérico
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Ocurrió un error' in str(message) for message in messages))
    
    def test_metodo_get_muestra_formulario_vacio(self):
        """CA1: Método GET muestra formulario vacío"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro.html')
        
        # Verificar que el formulario está vacío
        form = response.context['form']
        self.assertFalse(form.is_bound)  # Formulario no está vinculado a datos
    
    def test_csrf_exempt_funciona(self):
        """CA1: Verificar que @csrf_exempt funciona"""
        # Hacer POST sin CSRF token debería funcionar
        response = self.client.post(self.url, {})
        
        # No debería dar error 403 (CSRF Failure)
        self.assertNotEqual(response.status_code, 403)
