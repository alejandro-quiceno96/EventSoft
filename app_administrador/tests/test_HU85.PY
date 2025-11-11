from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from unittest.mock import patch


class GuardarMemoriasTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='12345678',
            first_name='Admin',
            last_name='Test'
        )
        
        # Crear perfil de administrador
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo'
        )
        
        # Crear evento sin memorias
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test Memorias',
            eve_descripcion='Descripción del evento test para memorias',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_memorias=''  # Sin memorias inicialmente
        )
        
        # Crear evento con memorias existentes
        self.evento_con_memorias = Eventos.objects.create(
            eve_nombre='Evento Con Memorias',
            eve_descripcion='Evento que ya tiene memorias',
            eve_ciudad='Medellín',
            eve_lugar='Auditorio Secundario',
            eve_fecha_inicio='2024-02-01',
            eve_fecha_fin='2024-02-02',
            eve_estado='Activo',
            eve_capacidad=80,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador,
            eve_memorias='https://drive.google.com/memorias-antiguas'  # Memorias existentes
        )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:guardar_memorias')
        
        # Probar con POST (el método que realmente usa la vista)
        response = self.client.post(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_metodo_get_no_permitido(self):
        """Prueba que GET retorne redirección al index"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        response = self.client.get(url)
        
        # Debería redirigir al index sin procesar
        self.assertEqual(response.status_code, 302)
        # Verificar la URL real de redirección en lugar del nombre
        self.assertTrue(response.url.startswith('/administrador/'))

    def test_guardar_memorias_exitoso(self):
        """Prueba que se puedan guardar memorias para un evento existente"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        # Datos para guardar memorias
        url_memorias = 'https://drive.google.com/memorias-evento-test'
        
        # Realizar petición POST para guardar memorias
        response = self.client.post(url, {
            'url_memorias': url_memorias,
            'evento_id': self.evento.id
        })
        
        # Verificar redirección exitosa con parámetro de éxito
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/administrador/'))
        self.assertIn('exito_memorias=1', response.url)
        
        # Verificar que las memorias se guardaron en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertEqual(evento_actualizado.eve_memorias, url_memorias)

    def test_actualizar_memorias_existentes(self):
        """Prueba que se puedan actualizar memorias existentes"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        # Nueva URL de memorias
        nueva_url_memorias = 'https://drive.google.com/memorias-actualizadas'
        
        # Verificar memorias existentes
        self.assertEqual(self.evento_con_memorias.eve_memorias, 'https://drive.google.com/memorias-antiguas')
        
        # Realizar petición POST para actualizar memorias
        response = self.client.post(url, {
            'url_memorias': nueva_url_memorias,
            'evento_id': self.evento_con_memorias.id
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('exito_memorias=1', response.url)
        
        # Verificar que las memorias se actualizaron en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento_con_memorias.id)
        self.assertEqual(evento_actualizado.eve_memorias, nueva_url_memorias)

    def test_guardar_memorias_evento_no_existente(self):
        """Prueba el comportamiento cuando se intenta guardar memorias para un evento que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        # Intentar guardar memorias para un ID de evento que no existe
        response = self.client.post(url, {
            'url_memorias': 'https://drive.google.com/memorias-test',
            'evento_id': 99999  # ID que no existe
        })
        
        # Debería redirigir al index (sin parámetro de éxito)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/administrador/'))
        self.assertNotIn('exito_memorias=1', response.url)
        
    def test_guardar_memorias_url_vacia(self):
        """Prueba que se pueda guardar una URL vacía (eliminar memorias)"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        # Guardar URL vacía
        response = self.client.post(url, {
            'url_memorias': '',  # URL vacía
            'evento_id': self.evento_con_memorias.id
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('exito_memorias=1', response.url)
        
        # Verificar que las memorias se eliminaron (campo vacío)
        evento_actualizado = Eventos.objects.get(id=self.evento_con_memorias.id)
        self.assertEqual(evento_actualizado.eve_memorias, '')

    def test_campos_requeridos(self):
        """Prueba que los campos requeridos estén presentes"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        # Enviar POST sin evento_id (campo requerido)
        response = self.client.post(url, {
            'url_memorias': 'https://drive.google.com/memorias-test'
            # Falta evento_id
        })
        
        # Debería redirigir al index (sin parámetro de éxito)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/administrador/'))
        self.assertNotIn('exito_memorias=1', response.url)



class GuardarMemoriasIntegrationTestCase(TestCase):
    """Pruebas de integración para el flujo completo de memorias"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin_integration',
            email='admin@integration.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='87654321'
        )
        
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo'
        )
        
        # Crear múltiples eventos
        self.eventos = []
        for i in range(3):
            evento = Eventos.objects.create(
                eve_nombre=f'Evento Integración {i}',
                eve_descripcion=f'Descripción evento {i}',
                eve_ciudad='Bogotá',
                eve_lugar=f'Auditorio {i}',
                eve_fecha_inicio='2024-01-01',
                eve_fecha_fin='2024-01-02',
                eve_estado='Activo',
                eve_capacidad=100,
                eve_tienecosto=False,
                eve_administrador_fk=self.administrador,
                eve_memorias=''
            )
            self.eventos.append(evento)

    def test_guardar_memorias_multiples_eventos(self):
        """Prueba guardar memorias para múltiples eventos secuencialmente"""
        self.client.login(username='admin_integration', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        urls_memorias = [
            'https://drive.google.com/memorias-evento-0',
            'https://drive.google.com/memorias-evento-1',
            'https://drive.google.com/memorias-evento-2'
        ]
        
        # Guardar memorias para cada evento
        for i, evento in enumerate(self.eventos):
            response = self.client.post(url, {
                'url_memorias': urls_memorias[i],
                'evento_id': evento.id
            })
            
            # Verificar redirección exitosa para cada operación
            self.assertEqual(response.status_code, 302)
            self.assertIn('exito_memorias=1', response.url)
            
            # Verificar que las memorias se guardaron correctamente
            evento_actualizado = Eventos.objects.get(id=evento.id)
            self.assertEqual(evento_actualizado.eve_memorias, urls_memorias[i])

    def test_actualizacion_concurrente_memorias(self):
        """Prueba el comportamiento con actualizaciones consecutivas"""
        self.client.login(username='admin_integration', password='testpass123')
        url = reverse('administrador:guardar_memorias')
        
        evento = self.eventos[0]
        
        # Primera actualización
        response1 = self.client.post(url, {
            'url_memorias': 'https://drive.google.com/primera-version',
            'evento_id': evento.id
        })
        
        # Segunda actualización
        response2 = self.client.post(url, {
            'url_memorias': 'https://drive.google.com/segunda-version',
            'evento_id': evento.id
        })
        
        # Tercera actualización
        response3 = self.client.post(url, {
            'url_memorias': 'https://drive.google.com/tercera-version',
            'evento_id': evento.id
        })
        
        # Verificar que la última actualización es la que persiste
        evento_actualizado = Eventos.objects.get(id=evento.id)
        self.assertEqual(evento_actualizado.eve_memorias, 'https://drive.google.com/tercera-version')
        
        # Verificar que todas las redirecciones fueron exitosas
        for response in [response1, response2, response3]:
            self.assertEqual(response.status_code, 302)
            self.assertIn('exito_memorias=1', response.url)
