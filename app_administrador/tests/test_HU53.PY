from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
import os
from unittest.mock import patch, MagicMock


class EliminarEventoTestCase(TestCase):
    
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
        
        # Crear eventos para pruebas
        self.evento_activo = Eventos.objects.create(
            eve_nombre='Evento Activo',
            eve_descripcion='Evento que se puede eliminar',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        self.evento_cerrado = Eventos.objects.create(
            eve_nombre='Evento Cerrado',
            eve_descripcion='Evento que NO se puede eliminar',
            eve_ciudad='Medellín',
            eve_lugar='Auditorio Secundario',
            eve_fecha_inicio='2024-02-01',
            eve_fecha_fin='2024-02-02',
            eve_estado='Cerrado',  # Estado que impide eliminación
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Archivos de prueba
        self.imagen_prueba = SimpleUploadedFile(
            "imagen_evento.jpg", 
            b"contenido_imagen", 
            content_type="image/jpeg"
        )
        
        self.programacion_prueba = SimpleUploadedFile(
            "programacion_evento.pdf", 
            b"contenido_pdf", 
            content_type="application/pdf"
        )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:eliminar_evento', args=[self.evento_activo.id])
        
        response = self.client.post(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_metodo_get_no_permitido(self):
        """Prueba que GET retorne método no permitido"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:eliminar_evento', args=[self.evento_activo.id])
        
        response = self.client.get(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertEqual(data['mensaje'], 'Método no permitido')

    def test_eliminar_evento_exitoso(self):
        """Prueba eliminar un evento activo exitosamente"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:eliminar_evento', args=[self.evento_activo.id])
        
        # Contar eventos antes de la eliminación
        eventos_count_before = Eventos.objects.count()
        
        # Realizar petición POST para eliminar evento
        response = self.client.post(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['mensaje'], 'Evento eliminado correctamente')
        
        # Verificar que se eliminó el evento de la base de datos
        eventos_count_after = Eventos.objects.count()
        self.assertEqual(eventos_count_after, eventos_count_before - 1)
        
        # Verificar que el evento específico ya no existe
        with self.assertRaises(Eventos.DoesNotExist):
            Eventos.objects.get(id=self.evento_activo.id)

    def test_eliminar_evento_cerrado(self):
        """Prueba que no se pueda eliminar un evento cerrado"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:eliminar_evento', args=[self.evento_cerrado.id])
        
        # Contar eventos antes del intento
        eventos_count_before = Eventos.objects.count()
        
        # Intentar eliminar evento cerrado
        response = self.client.post(url)
        
        # Verificar respuesta de error
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['mensaje'], 'No se puede eliminar un evento cerrado.')
        
        # Verificar que el evento NO se eliminó
        eventos_count_after = Eventos.objects.count()
        self.assertEqual(eventos_count_after, eventos_count_before)
        
        # Verificar que el evento cerrado sigue existiendo
        evento_cerrado = Eventos.objects.get(id=self.evento_cerrado.id)
        self.assertEqual(evento_cerrado.eve_estado, 'Cerrado')


    def test_eliminar_evento_no_existente(self):
        """Prueba eliminar un evento que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:eliminar_evento', args=[99999])  # ID que no existe
        
        response = self.client.post(url)
        
        # Debería retornar 404 Not Found
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['mensaje'], 'Evento no encontrado')

    def test_eliminar_evento_sin_archivos(self):
        """Prueba eliminar evento sin archivos asociados"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Crear evento sin archivos
        evento_sin_archivos = Eventos.objects.create(
            eve_nombre='Evento Sin Archivos',
            eve_descripcion='Evento sin imagen ni programación',
            eve_ciudad='Barranquilla',
            eve_lugar='Auditorio',
            eve_fecha_inicio='2024-04-01',
            eve_fecha_fin='2024-04-02',
            eve_estado='Activo',
            eve_capacidad=80,
            eve_administrador_fk=self.administrador
            # Sin eve_imagen ni eve_programacion
        )
        
        url = reverse('administrador:eliminar_evento', args=[evento_sin_archivos.id])
        
        response = self.client.post(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['mensaje'], 'Evento eliminado correctamente')
        
        # Verificar que el evento fue eliminado
        with self.assertRaises(Eventos.DoesNotExist):
            Eventos.objects.get(id=evento_sin_archivos.id)
