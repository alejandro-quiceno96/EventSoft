import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_administrador.models import Administradores

User = get_user_model()

class SuspenderCancelarAdministradorTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # Crear administradores para testing
        self.admin_user1 = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='111111111'
        )
        
        self.admin_user2 = User.objects.create_user(
            username='admin2',
            email='admin2@example.com', 
            password='testpass123',
            tipo_documento='CE',
            documento_identidad='222222222'
        )
        
        self.administrador1 = Administradores.objects.create(
            usuario=self.admin_user1,
            estado='Activo',
            clave_acceso='CLAVE123'
        )
        
        self.administrador2 = Administradores.objects.create(
            usuario=self.admin_user2,
            estado='Activo', 
            clave_acceso='CLAVE456'
        )
        
        # URL para los tests
        self.url = reverse('super_admin:cancelar_administrador')  # Ajustar según tu URL name
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def test_eliminacion_administrador_existente(self):
        """CA1: Eliminación exitosa de un administrador existente"""
        # Verificar que el administrador existe antes de la eliminación
        self.assertTrue(Administradores.objects.filter(id=self.administrador1.id).exists())
        
        # Realizar solicitud POST para eliminar
        data = {
            "admin_id": self.administrador1.id
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que el administrador fue eliminado
        self.assertFalse(Administradores.objects.filter(id=self.administrador1.id).exists())
    
    def test_eliminacion_administrador_inexistente(self):
        """CA2: Manejo de error cuando el administrador no existe"""
        admin_id_inexistente = 9999
        
        data = {
            "admin_id": admin_id_inexistente
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta de error
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        self.assertIn('Administradores matching query does not exist', response_data['error'])
    
    def test_metodo_get_no_permitido(self):
        """CA2: Método GET retorna error"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')
    
    def test_metodo_put_no_permitido(self):
        """CA2: Método PUT retorna error"""
        response = self.client.put(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')
    
    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        response = client_no_auth.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_estructura_respuesta_exitosa(self):
        """CA3: Respuesta JSON tiene estructura correcta en caso de éxito"""
        data = {
            "admin_id": self.administrador2.id
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = response.json()
        
        # Verificar estructura de respuesta exitosa
        self.assertEqual(response_data['success'], True)
        self.assertNotIn('error', response_data)  # No debe haber error en éxito
    
    def test_estructura_respuesta_error(self):
        """CA3: Respuesta JSON tiene estructura correcta en caso de error"""
        data = {
            "admin_id": 9999  # ID inexistente
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        response_data = response.json()
        
        # Verificar estructura de respuesta de error
        self.assertEqual(response_data['success'], False)
        self.assertIn('error', response_data)
        self.assertIsInstance(response_data['error'], str)
    
    def test_datos_invalidos_json(self):
        """CA2: Manejo de datos JSON malformados"""
        # Enviar datos no JSON
        response = self.client.post(
            self.url,
            data="esto no es json",
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_falta_admin_id(self):
        """CA2: Manejo de solicitud sin admin_id"""
        data = {}  # Sin admin_id
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_eliminacion_multiple_administradores(self):
        """CA1: Eliminación secuencial de múltiples administradores"""
        # Crear un tercer administrador para esta prueba
        admin_user3 = User.objects.create_user(
            username='admin3',
            email='admin3@example.com',
            password='testpass123'
        )
        administrador3 = Administradores.objects.create(
            usuario=admin_user3,
            estado='Activo',
            clave_acceso='CLAVE789'
        )
        
        # Verificar administradores iniciales
        self.assertEqual(Administradores.objects.count(), 3)
        
        # Eliminar primer administrador
        data1 = {"admin_id": self.administrador1.id}
        response1 = self.client.post(
            self.url,
            data=json.dumps(data1),
            content_type='application/json'
        )
        self.assertTrue(response1.json()['success'])
        self.assertEqual(Administradores.objects.count(), 2)
        
        # Eliminar segundo administrador
        data2 = {"admin_id": administrador3.id}
        response2 = self.client.post(
            self.url,
            data=json.dumps(data2),
            content_type='application/json'
        )
        self.assertTrue(response2.json()['success'])
        self.assertEqual(Administradores.objects.count(), 1)
    
    def test_csrf_exempt_funciona(self):
        """Verificar que CSRF exempt permite la solicitud sin token CSRF"""
        # Esta prueba verifica que @csrf_exempt funciona correctamente
        data = {
            "admin_id": self.administrador1.id
        }
        
        # El cliente de prueba normalmente manejaría CSRF, pero verificamos que no falle
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # La solicitud debería procesarse sin errores CSRF
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])