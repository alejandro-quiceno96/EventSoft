from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import datetime
from app_eventos.models import Eventos, EventosCategorias
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores
from app_usuarios.models import Usuario as User
from app_areas.models import Areas
from app_categorias.models import Categorias
import json


class CrearEventoTestCase(TestCase):
    
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
        
        # Crear perfil de administrador con eventos disponibles
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo',
            num_eventos=5  # Tiene 5 eventos disponibles
        )
        
        # Crear superadministradores para notificaciones
        self.superadmin1_user = User.objects.create_user(
            username='superadmin1',
            email='superadmin1@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='11111111'
        )
        
        self.superadmin2_user = User.objects.create_user(
            username='superadmin2',
            email='superadmin2@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='22222222'
        )
        
        self.superadmin1 = SuperAdministradores.objects.create(usuario=self.superadmin1_user)
        self.superadmin2 = SuperAdministradores.objects.create(usuario=self.superadmin2_user)
        
        # Crear área y categoría para el evento
        self.area = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología'
        )
        
        self.categoria = Categorias.objects.create(
            cat_nombre='Desarrollo Web',
            cat_area_fk=self.area
        )
        
        # Archivos de prueba
        self.imagen_evento = SimpleUploadedFile(
            "evento.jpg", 
            b"file_content", 
            content_type="image/jpeg"
        )
        
        self.documento_programacion = SimpleUploadedFile(
            "programacion.pdf", 
            b"file_content", 
            content_type="application/pdf"
        )
        
        # Datos del evento
        self.datos_evento = {
            'nombre_evento': 'Evento de Prueba 2024',
            'descripcion_evento': 'Descripción detallada del evento de prueba',
            'ciudad': 'Bogotá',
            'lugar': 'Auditorio Principal',
            'fecha_inicio': '2024-12-01',
            'fecha_fin': '2024-12-02',
            'categoria': str(self.categoria.id),
            'inscripcion': 'Si',  # Con costo
            'permitir_participantes': '1',  # Permitir participantes
            'cantidad_personas': '100'
        }

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:crear_evento')
        
        response = self.client.get(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_acceso_vista_con_autenticacion(self):
        """Prueba que la vista sea accesible para administradores autenticados"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertIn('areas', response.context)
        self.assertIn('administrador', response.context)

    def test_crear_evento_exitoso(self):
        """Prueba crear un evento exitosamente con todos los datos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        # Contar eventos antes de la creación
        eventos_count_before = Eventos.objects.count()
        
        # Realizar petición POST para crear evento
        response = self.client.post(url, {
            **self.datos_evento,
            'imagen_evento': self.imagen_evento,
            'documento_evento': self.documento_programacion
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('revision=evento', response.url)
        
        # Verificar que se creó el evento en la base de datos
        eventos_count_after = Eventos.objects.count()
        self.assertEqual(eventos_count_after, eventos_count_before + 1)
        
        # Verificar datos del evento creado
        evento_creado = Eventos.objects.last()
        self.assertEqual(evento_creado.eve_nombre, 'Evento de Prueba 2024')
        self.assertEqual(evento_creado.eve_ciudad, 'Bogotá')
        self.assertEqual(evento_creado.eve_estado, 'Pendiente')
        self.assertEqual(evento_creado.eve_capacidad, 100)
        self.assertTrue(evento_creado.eve_tienecosto)
        self.assertEqual(evento_creado.eve_administrador_fk, self.administrador)
        
        # Verificar relación con categoría
        relacion_categoria = EventosCategorias.objects.filter(eve_cat_evento_fk=evento_creado).first()
        self.assertIsNotNone(relacion_categoria)
        self.assertEqual(relacion_categoria.eve_cat_categoria_fk, self.categoria)

    def test_actualizacion_contador_administrador(self):
        """Prueba que se actualice el contador de eventos del administrador"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        contador_inicial = self.administrador.num_eventos
        
        # Crear evento
        response = self.client.post(url, self.datos_evento)
        
        # Verificar que el contador disminuyó en 1
        administrador_actualizado = Administradores.objects.get(id=self.administrador.id)
        self.assertEqual(administrador_actualizado.num_eventos, contador_inicial - 1)

    def test_crear_evento_sin_participantes(self):
        """Prueba crear evento sin permitir participantes"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        datos_sin_participantes = {
            **self.datos_evento,
            'permitir_participantes': '0',  # No permitir participantes
            # No enviar cantidad_personas
        }
        
        response = self.client.post(url, datos_sin_participantes)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar datos del evento
        evento_creado = Eventos.objects.last()
        self.assertEqual(evento_creado.eve_capacidad, 0)  # Capacidad 0 cuando no hay participantes

    def test_crear_evento_sin_costo(self):
        """Prueba crear evento sin costo de inscripción"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        datos_sin_costo = {
            **self.datos_evento,
            'inscripcion': 'No'  # Sin costo
        }
        
        response = self.client.post(url, datos_sin_costo)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar datos del evento
        evento_creado = Eventos.objects.last()
        self.assertFalse(evento_creado.eve_tienecosto)  # Debe ser False

    def test_crear_evento_sin_archivos(self):
        """Prueba crear evento sin archivos adjuntos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:crear_evento')
        
        response = self.client.post(url, self.datos_evento)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el evento se creó sin archivos
        evento_creado = Eventos.objects.last()
        self.assertEqual(evento_creado.eve_nombre, 'Evento de Prueba 2024')
        self.assertFalse(bool(evento_creado.eve_imagen))  # Sin imagen
        self.assertFalse(bool(evento_creado.eve_programacion))  # Sin programación
