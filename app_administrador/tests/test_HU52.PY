from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages
from app_eventos.models import Eventos, EventosCategorias
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from app_areas.models import Areas
from app_categorias.models import Categorias
from unittest.mock import patch, MagicMock
import os


class EditarEventoTestCase(TestCase):
    
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
        
        # Crear áreas y categorías
        self.area_tecnologia = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología'
        )
        
        self.area_ciencias = Areas.objects.create(
            are_nombre='Ciencias',
            are_descripcion='Área de ciencias'
        )
        
        self.categoria_web = Categorias.objects.create(
            cat_nombre='Desarrollo Web',
            cat_area_fk=self.area_tecnologia
        )
        
        self.categoria_movil = Categorias.objects.create(
            cat_nombre='Desarrollo Móvil',
            cat_area_fk=self.area_tecnologia
        )
        
        self.categoria_fisica = Categorias.objects.create(
            cat_nombre='Física',
            cat_area_fk=self.area_ciencias
        )
        
        # Crear evento para editar
        self.evento_editable = Eventos.objects.create(
            eve_nombre='Evento Original',
            eve_descripcion='Descripción original',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Original',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Asignar categoría al evento
        self.evento_categoria = EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_editable,
            eve_cat_categoria_fk=self.categoria_web
        )
        
        # Crear evento cerrado (no editable)
        self.evento_cerrado = Eventos.objects.create(
            eve_nombre='Evento Cerrado',
            eve_descripcion='Evento cerrado no editable',
            eve_ciudad='Medellín',
            eve_lugar='Auditorio Cerrado',
            eve_fecha_inicio='2024-02-01',
            eve_fecha_fin='2024-02-02',
            eve_estado='Cerrado',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Archivos de prueba
        self.nueva_imagen = SimpleUploadedFile(
            "nueva_imagen.jpg", 
            b"contenido_imagen_nueva", 
            content_type="image/jpeg"
        )
        
        self.nueva_programacion = SimpleUploadedFile(
            "nueva_programacion.pdf", 
            b"contenido_pdf_nuevo", 
            content_type="application/pdf"
        )
        
        # Datos actualizados para el evento
        self.datos_actualizados = {
            'nombre_evento': 'Evento Actualizado 2024',
            'descripcion_evento': 'Descripción actualizada del evento',
            'ciudad': 'Cali',
            'lugar': 'Auditorio Actualizado',
            'fecha_inicio': '2024-12-01',
            'fecha_fin': '2024-12-03',
            'categoria': str(self.categoria_movil.id),
            'inscripcion': 'Si',  # Con costo
            'estado_evento': 'Finalizado',
            'cantidad_personas': '200'
        }

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        response = self.client.get(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_acceso_vista_con_autenticacion(self):
        """Prueba que la vista sea accesible para administradores autenticados"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertIn('evento', response.context)
        self.assertIn('areas', response.context)
        self.assertIn('categorias', response.context)
        self.assertIn('categoria_seleccionada', response.context)
        self.assertIn('area_seleccionada', response.context)

    def test_editar_evento_exitoso(self):
        """Prueba editar un evento exitosamente con todos los datos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        # Realizar petición POST para editar evento
        response = self.client.post(url, self.datos_actualizados)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el evento fue actualizado en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento_editable.id)
        self.assertEqual(evento_actualizado.eve_nombre, 'Evento Actualizado 2024')
        self.assertEqual(evento_actualizado.eve_descripcion, 'Descripción actualizada del evento')
        self.assertEqual(evento_actualizado.eve_ciudad, 'Cali')
        self.assertEqual(evento_actualizado.eve_lugar, 'Auditorio Actualizado')
        self.assertEqual(evento_actualizado.eve_capacidad, 200)
        self.assertTrue(evento_actualizado.eve_tienecosto)
        self.assertEqual(evento_actualizado.eve_estado, 'Finalizado')
        
        # Verificar que la categoría fue actualizada
        relacion_categoria_actualizada = EventosCategorias.objects.get(eve_cat_evento_fk=self.evento_editable)
        self.assertEqual(relacion_categoria_actualizada.eve_cat_categoria_fk, self.categoria_movil)

    def test_editar_evento_con_archivos(self):
        """Prueba editar evento actualizando archivos adjuntos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        datos_con_archivos = {
            **self.datos_actualizados,
            'imagen_evento': self.nueva_imagen,
            'documento_evento': self.nueva_programacion
        }
        
        # Usar mock para verificar eliminación de archivos antiguos
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            
            response = self.client.post(url, datos_con_archivos)
            
            # Verificar redirección exitosa
            self.assertEqual(response.status_code, 302)
            
            # Verificar que el evento fue actualizado
            evento_actualizado = Eventos.objects.get(id=self.evento_editable.id)
            self.assertEqual(evento_actualizado.eve_nombre, 'Evento Actualizado 2024')

    def test_editar_evento_sin_archivos(self):
        """Prueba editar evento sin cambiar los archivos adjuntos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        # Enviar datos sin archivos
        response = self.client.post(url, self.datos_actualizados)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el evento fue actualizado
        evento_actualizado = Eventos.objects.get(id=self.evento_editable.id)
        self.assertEqual(evento_actualizado.eve_nombre, 'Evento Actualizado 2024')

    def test_editar_evento_sin_aforo(self):
        """Prueba editar evento sin especificar aforo"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        datos_sin_aforo = {
            **self.datos_actualizados,
            'cantidad_personas': ''  # Aforo vacío
        }
        
        response = self.client.post(url, datos_sin_aforo)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el aforo se estableció en 0
        evento_actualizado = Eventos.objects.get(id=self.evento_editable.id)
        self.assertEqual(evento_actualizado.eve_capacidad, 0)

    def test_editar_evento_sin_costo(self):
        """Prueba editar evento sin costo de inscripción"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        datos_sin_costo = {
            **self.datos_actualizados,
            'inscripcion': 'No'  # Sin costo
        }
        
        response = self.client.post(url, datos_sin_costo)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el costo se estableció en False
        evento_actualizado = Eventos.objects.get(id=self.evento_editable.id)
        self.assertFalse(evento_actualizado.eve_tienecosto)

    def test_editar_evento_cerrado(self):
        """Prueba que no se pueda editar un evento cerrado"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_cerrado.id])
        
        response = self.client.get(url)
        
        # Debería redirigir al index con mensaje de error
        self.assertEqual(response.status_code, 302)

    def test_contexto_vista_get(self):
        """Prueba el contexto de la vista GET"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:editar_evento', args=[self.evento_editable.id])
        
        response = self.client.get(url)
        
        # Verificar contexto
        contexto = response.context
        self.assertEqual(contexto['evento'], self.evento_editable)
        self.assertEqual(contexto['categoria_seleccionada'], self.categoria_web)
        self.assertEqual(contexto['area_seleccionada'], self.area_tecnologia)
        self.assertIn('areas', contexto)
        self.assertIn('categorias', contexto)

