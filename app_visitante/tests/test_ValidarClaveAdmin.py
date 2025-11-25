import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_administrador.models import Administradores

User = get_user_model()

class ValidarClaveAdminTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.url = reverse('validar_clave_admin')  # Ajusta según tu URL name
        
        # Crear usuarios de prueba
        self.user_admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.user_normal = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='testpass123'
        )
        
        # Crear administrador con clave de acceso
        self.administrador = Administradores.objects.create(
            usuario=self.user_admin,
            estado='Creado',  # Estado inicial
            clave_acceso='CLAVE123'
        )
    
    def test_validacion_clave_correcta(self):
        """CA1: Clave correcta activa la cuenta y retorna éxito"""
        # Autenticar como administrador
        self.client.login(username='adminuser', password='testpass123')
        
        data = {
            'clave': 'CLAVE123'
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
        self.assertTrue(response_data['success'])
        self.assertNotIn('error', response_data)
        
        # Verificar que el administrador fue activado
        administrador_actualizado = Administradores.objects.get(usuario=self.user_admin)
        self.assertEqual(administrador_actualizado.estado, 'Activo')
    
    def test_clave_incorrecta(self):
        """CA2: Clave incorrecta retorna error sin activar cuenta"""
        self.client.login(username='adminuser', password='testpass123')
        
        data = {
            'clave': 'CLAVE_INCORRECTA'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta exitosa pero con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Clave incorrecta')
        
        # Verificar que el estado NO cambió
        administrador_actual = Administradores.objects.get(usuario=self.user_admin)
        self.assertEqual(administrador_actual.estado, 'Creado')  # Estado original
    
    def test_usuario_sin_administrador(self):
        """CA3: Usuario sin registro de administrador retorna error"""
        self.client.login(username='normaluser', password='testpass123')
        
        data = {
            'clave': 'CLAVE123'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Clave incorrecta')
    
    def test_metodo_get_no_permitido(self):
        """CA3: Método GET retorna error"""
        self.client.login(username='adminuser', password='testpass123')
        
        response = self.client.get(self.url)
        
        # Verificar respuesta con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')
    
    def test_json_malformado(self):
        """CA3: JSON malformado retorna error"""
        self.client.login(username='adminuser', password='testpass123')
        
        response = self.client.post(
            self.url,
            data='{json malformado}',
            content_type='application/json'
        )
        
        # Verificar respuesta con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
    
    def test_campo_clave_faltante(self):
        """CA3: Campo clave faltante en JSON"""
        self.client.login(username='adminuser', password='testpass123')
        
        data = {
            'otro_campo': 'valor'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        # Depende de cómo maneje el .get() - podría ser None y fallar en la comparación
    
    def test_clave_vacia(self):
        """CA2: Clave vacía retorna error"""
        self.client.login(username='adminuser', password='testpass123')
        
        data = {
            'clave': ''
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta con error
        self.assertEqual(response.status_code, 200)
        
        # Verificar contenido JSON
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Clave incorrecta')
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado (debería redirigir por @login_required)"""
        data = {
            'clave': 'CLAVE123'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # @login_required debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)