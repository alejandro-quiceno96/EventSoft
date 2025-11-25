import json
from django.test import TestCase, Client
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from app_usuarios.models import Usuario as User

class VerificarDocumentoTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.url = reverse('verificar_documento')  # Ajusta según tu URL name
        
        # Crear usuario de prueba con documento
        self.user_existente = User.objects.create_user(
            username='usuarioprueba',
            email='test@example.com',
            password='testpass123',
            documento_identidad='123456789'
        )
    
    def test_verificar_documento_existente(self):
        """CA1: Documento existente retorna True"""
        data = {
            'documento_identidad': '123456789'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertIn('existe', response_data)
        self.assertTrue(response_data['existe'])
    
    def test_verificar_documento_no_existente(self):
        """CA1: Documento no existente retorna False"""
        data = {
            'documento_identidad': '999999999'  # Documento que no existe
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertIn('existe', response_data)
        self.assertFalse(response_data['existe'])
    
    def test_documento_vacio(self):
        """CA2: Documento vacío retorna error 400"""
        data = {
            'documento_identidad': ''  # Documento vacío
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar error 400
        self.assertEqual(response.status_code, 400)
        
        # Verificar mensaje de error
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Documento no proporcionado.')
    
    def test_documento_nulo(self):
        """CA2: Documento nulo retorna error 400"""
        data = {
            'documento_identidad': None  # Documento nulo
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar error 400
        self.assertEqual(response.status_code, 400)
        
        # Verificar mensaje de error
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Documento no proporcionado.')
    
    def test_campo_documento_faltante(self):
        """CA2: Campo documento_identidad faltante retorna error 400"""
        data = {
            'otro_campo': 'valor'  # Campo incorrecto
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar error 400
        self.assertEqual(response.status_code, 400)
        
        # Verificar mensaje de error
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Documento no proporcionado.')
    
    def test_json_malformado(self):
        """CA2: JSON malformado retorna error 400"""
        response = self.client.post(
            self.url,
            data='{json malformado}',  # JSON inválido
            content_type='application/json'
        )
        
        # Verificar error 400
        self.assertEqual(response.status_code, 400)
        
        # Verificar mensaje de error
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Datos inválidos.')
    
    def test_metodo_get_no_permitido(self):
        """CA3: Método GET retorna error 405"""
        response = self.client.get(self.url)
        
        # Verificar error 405 (Method Not Allowed)
        self.assertEqual(response.status_code, 405)
    
    def test_metodo_put_no_permitido(self):
        """CA3: Método PUT retorna error 405"""
        response = self.client.put(self.url)
        
        # Verificar error 405 (Method Not Allowed)
        self.assertEqual(response.status_code, 405)
    
    def test_metodo_delete_no_permitido(self):
        """CA3: Método DELETE retorna error 405"""
        response = self.client.delete(self.url)
        
        # Verificar error 405 (Method Not Allowed)
        self.assertEqual(response.status_code, 405)
    
    def test_content_type_no_json(self):
        """CA2: Content-Type no JSON podría causar error"""
        data = {
            'documento_identidad': '123456789'
        }
        
        response = self.client.post(
            self.url,
            data=data,  # Sin content_type application/json
            # content_type='application/x-www-form-urlencoded' por defecto
        )
        
        # Dependiendo de la implementación, podría dar error 400 o 500
        self.assertIn(response.status_code, [400, 500])

