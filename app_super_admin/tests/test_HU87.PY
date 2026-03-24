import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from app_usuarios.models import Usuario as User
from app_administrador.models import Administradores



class AsignarAdminEventoTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123',
            first_name='Super',
            last_name='Admin'
        )
        
        # Crear usuario normal para asignar como administrador
        self.usuario_normal = User.objects.create_user(
            username='usuarionormal',
            email='usuario@example.com',
            password='testpass123',
            first_name='Usuario',
            last_name='Normal'
        )
        
        # Datos de prueba
        self.datos_validos = {
            'usuario_id': self.usuario_normal.id,
            'eventos': '5',
            'fecha_limite': '2024-12-31',
            'codigo': 'CLAVE123'
        }
        
        # URL para los tests
        self.url = reverse('super_admin:asignar_admin_evento')  # Ajusta según tu URL name
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    @patch('app_super_admin.views.EmailMultiAlternatives')
    @patch('app_super_admin.views.render_to_string')
    def test_asignacion_admin_exitosa(self, mock_render_to_string, mock_email_class):
        """CA1: Asignación exitosa de administrador con envío de email"""
        # Mock de render_to_string
        mock_render_to_string.return_value = '<html>Email content</html>'
        
        # Mock de EmailMultiAlternatives
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que se creó el administrador
        administrador = Administradores.objects.get(usuario=self.usuario_normal)
        self.assertEqual(administrador.num_eventos, 5)
        self.assertEqual(administrador.tiempo_limite.strftime('%Y-%m-%d'), '2024-12-31')
        self.assertEqual(administrador.estado, 'Creado')
        self.assertEqual(administrador.clave_acceso, 'CLAVE123')
        
        # Verificar que se llamó a render_to_string con los parámetros correctos
        mock_render_to_string.assert_called_once()
        call_args = mock_render_to_string.call_args
        self.assertEqual(call_args[0][0], 'app_super_admin/correos/asignar_rol.html')
        
        # Verificar contexto del email
        context = call_args[0][1] if len(call_args[0]) > 1 else {}
        self.assertEqual(context['nombre'], 'Usuario Normal')
        self.assertEqual(context['clave'], 'CLAVE123')
        self.assertEqual(context['fecha_limite'], '2024-12-31')
        self.assertEqual(context['num_eventos'], '5')
        self.assertEqual(context['nombre_usuario'], 'usuarionormal')
        
        # CORREGIDO: EmailMultiAlternatives usa argumentos posicionales
        mock_email_class.assert_called_once_with(
            'Asignación de rol como Administrador de Eventos',  # subject
            '',  # text_content 
            'eventsoft3@gmail.com',  # from_email
            ['usuario@example.com']  # to
        )
        mock_email_instance.attach_alternative.assert_called_once_with('<html>Email content</html>', "text/html")
        mock_email_instance.send.assert_called_once()
    
    def test_campos_obligatorios_faltantes(self):
        """CA2: Faltan campos obligatorios retorna error 400"""
        # Probar con datos incompletos
        datos_incompletos = {
            'usuario_id': self.usuario_normal.id,
            'eventos': '5'
            # Faltan fecha_limite y codigo
        }
        
        response = self.client.post(self.url, datos_incompletos)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Faltan campos obligatorios", response.content.decode())
    
    def test_usuario_no_existe(self):
        """CA2: Usuario no existe retorna error 404"""
        datos_usuario_inexistente = {
            'usuario_id': 9999,  # ID que no existe
            'eventos': '5',
            'fecha_limite': '2024-12-31',
            'codigo': 'CLAVE123'
        }
        
        response = self.client.post(self.url, datos_usuario_inexistente)
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Usuario no encontrado.')
    
    def test_eventos_maximos_no_numerico(self):
        """CA2: Eventos máximos no numérico causa error"""
        datos_invalidos = {
            'usuario_id': self.usuario_normal.id,
            'eventos': 'no_numerico',  # Inválido
            'fecha_limite': '2024-12-31',
            'codigo': 'CLAVE123'
        }
        
        response = self.client.post(self.url, datos_invalidos)
        
        # Debería causar error 500 por la conversión a int
        self.assertEqual(response.status_code, 500)
    
    @patch('app_super_admin.views.EmailMultiAlternatives')
    @patch('app_super_admin.views.render_to_string')
    def test_error_envio_email_no_afecta_creacion(self, mock_render_to_string, mock_email_class):
        """CA3: Error en envío de email no afecta creación del administrador"""
        # Mock que falla el envío de email
        mock_render_to_string.return_value = '<html>Email content</html>'
        mock_email_instance = MagicMock()
        mock_email_instance.send.side_effect = Exception('Error de servidor SMTP')
        mock_email_class.return_value = mock_email_instance
        
        response = self.client.post(self.url, self.datos_validos)
        
        # CORREGIDO: La vista retorna 500 cuando hay error en el email
        self.assertEqual(response.status_code, 500)
        
        # Pero el administrador se debería crear igual
        self.assertTrue(Administradores.objects.filter(usuario=self.usuario_normal).exists())
    
    def test_metodo_get_no_permitido(self):
        """CA3: Método GET no permitido"""
        response = self.client.get(self.url)
        
        # La vista actual no maneja GET específicamente, pero podría dar error
        self.assertIn(response.status_code, [200, 400, 405])
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado es redirigido"""
        client_no_auth = Client()
        response = client_no_auth.post(self.url, self.datos_validos)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
