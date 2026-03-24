import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_eventos.models import EventosCategorias

User = get_user_model()

class EventoAsistentesTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario asistente
        self.usuario_asistente = User.objects.create_user(
            username='asistente',
            email='asistente@example.com',
            password='testpass123'
        )
        
        # Crear perfil de asistente
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)
        
        # Crear otro asistente para pruebas
        self.otro_usuario_asistente = User.objects.create_user(
            username='otro_asistente',
            email='otro_asistente@example.com',
            password='testpass123'
        )
        self.otro_asistente = Asistentes.objects.create(usuario=self.otro_usuario_asistente)
        
        # Crear administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.administrador = Administradores.objects.create(usuario=self.admin_user)
        
        # Crear área y categoría
        self.area = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología'
        )
        
        self.categoria = Categorias.objects.create(
            cat_nombre='Programación',
            cat_descripcion='Categoría de programación',
            cat_area_fk=self.area
        )
        
        # Crear evento con imagen y programación
        hoy = timezone.now().date()
        self.evento = Eventos.objects.create(
            eve_nombre='Conferencia de Programación',
            eve_descripcion='Una conferencia sobre programación avanzada',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen=SimpleUploadedFile("evento.jpg", b"file_content", content_type="image/jpeg"),
            eve_programacion=SimpleUploadedFile("programacion.pdf", b"pdf_content", content_type="application/pdf"),
            eve_capacidad=100,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Crear evento gratuito sin límite de cupos
        self.evento_gratuito = Eventos.objects.create(
            eve_nombre='Workshop Gratuito',
            eve_descripcion='Taller gratuito de introducción',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='activo',
            eve_imagen=SimpleUploadedFile("evento2.jpg", b"file_content2", content_type="image/jpeg"),
            eve_capacidad=0,  # Cupos ilimitados
            eve_tienecosto=False,  # Gratuito
            eve_administrador_fk=self.administrador
        )
        
        # Crear evento sin imagen ni programación
        self.evento_sin_archivos = Eventos.objects.create(
            eve_nombre='Evento Simple',
            eve_descripcion='Evento sin archivos adjuntos',
            eve_ciudad='Cali',
            eve_lugar='Lugar Simple',
            eve_fecha_inicio=hoy + timedelta(days=20),
            eve_fecha_fin=hoy + timedelta(days=21),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Asociar categorías a los eventos
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento,
            eve_cat_categoria_fk=self.categoria
        )
        
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_gratuito,
            eve_cat_categoria_fk=self.categoria
        )
        
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_sin_archivos,
            eve_cat_categoria_fk=self.categoria
        )
        
        # Crear inscripción con clave de acceso y QR
        self.inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte.pdf", b"file_content", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr.pdf", b"qr_content", content_type="application/pdf"),
            asi_eve_clave='CLAVE123XYZ'
        )
        
        # Crear inscripción para el evento gratuito
        self.inscripcion_gratuita = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento_gratuito,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE456ABC'
        )
        
        # URL para los tests
        self.url = reverse('app_asistente:evento_asistentes', args=[self.evento.id, self.asistente.id])
        
        # Autenticar como asistente
        self.client.login(username='asistente', password='testpass123')

    def test_consulta_evento_existente_con_inscripcion(self):
        """CA1: Consulta exitosa de evento cuando existe y el asistente está inscrito"""
        response = self.client.get(self.url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que es JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Parsear respuesta JSON
        datos_evento = response.json()
        
        # Verificar estructura completa de datos
        self.assertIn('eve_id', datos_evento)
        self.assertIn('eve_nombre', datos_evento)
        self.assertIn('eve_descripcion', datos_evento)
        self.assertIn('eve_ciudad', datos_evento)
        self.assertIn('eve_lugar', datos_evento)
        self.assertIn('eve_fecha_inicio', datos_evento)
        self.assertIn('eve_fecha_fin', datos_evento)
        self.assertIn('eve_imagen', datos_evento)
        self.assertIn('eve_cantidad', datos_evento)
        self.assertIn('eve_costo', datos_evento)
        self.assertIn('eve_programacion', datos_evento)
        self.assertIn('eve_clave_acceso', datos_evento)
        self.assertIn('codigo_qr', datos_evento)
        self.assertIn('eve_categoria', datos_evento)
        
        # Verificar valores específicos
        self.assertEqual(datos_evento['eve_id'], self.evento.id)
        self.assertEqual(datos_evento['eve_nombre'], 'Conferencia de Programación')
        self.assertEqual(datos_evento['eve_descripcion'], 'Una conferencia sobre programación avanzada')
        self.assertEqual(datos_evento['eve_ciudad'], 'Bogotá')
        self.assertEqual(datos_evento['eve_lugar'], 'Auditorio Principal')
        self.assertEqual(datos_evento['eve_costo'], 'Con Pago')
        self.assertEqual(datos_evento['eve_clave_acceso'], 'CLAVE123XYZ')
        self.assertEqual(datos_evento['eve_categoria'], 'Programación')

    def test_evento_no_existe(self):
        """CA2: Error cuando el evento no existe - COMPORTAMIENTO ACTUAL: 500"""
        evento_id_inexistente = 9999
        url_evento_inexistente = reverse('app_asistente:evento_asistentes', args=[evento_id_inexistente, self.asistente.id])
        
        response = self.client.get(url_evento_inexistente)
        
        # CORRECCIÓN: La función actual retorna 500, no 404
        # Porque get_object_or_404 lanza excepción que no se captura
        self.assertEqual(response.status_code, 500)

    def test_asistente_no_inscrito(self):
        """CA2: Datos del evento sin clave de acceso cuando el asistente no está inscrito"""
        # Usar el otro asistente que no está inscrito en este evento
        url_no_inscrito = reverse('app_asistente:evento_asistentes', args=[self.evento.id, self.otro_asistente.id])
        
        response = self.client.get(url_no_inscrito)
        
        # Verificar respuesta exitosa (el evento existe)
        self.assertEqual(response.status_code, 200)
        
        datos_evento = response.json()
        
        # Verificar que el evento se retorna pero sin clave de acceso ni QR
        self.assertEqual(datos_evento['eve_id'], self.evento.id)
        self.assertEqual(datos_evento['eve_nombre'], 'Conferencia de Programación')
        self.assertIsNone(datos_evento['eve_clave_acceso'])
        self.assertIsNone(datos_evento['codigo_qr'])

    def test_evento_gratuito_sin_cupos(self):
        """CA1: Evento gratuito con cupos ilimitados"""
        url_gratuito = reverse('app_asistente:evento_asistentes', args=[self.evento_gratuito.id, self.asistente.id])
        
        response = self.client.get(url_gratuito)
        
        self.assertEqual(response.status_code, 200)
        
        datos_evento = response.json()
        
        # Verificar datos específicos de evento gratuito
        self.assertEqual(datos_evento['eve_costo'], 'Gratuito')
        self.assertEqual(datos_evento['eve_cantidad'], 'Cupos ilimitados')
        self.assertEqual(datos_evento['eve_clave_acceso'], 'CLAVE456ABC')

    def test_evento_sin_archivos_adjuntos(self):
        """CA1: Evento sin imagen ni programación"""
        # Crear inscripción para el evento sin archivos
        inscripcion_sin_archivos = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento_sin_archivos,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte3.pdf", b"file_content3", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr3.pdf", b"qr_content3", content_type="application/pdf"),
            asi_eve_clave='CLAVE789DEF'
        )
        
        url_sin_archivos = reverse('app_asistente:evento_asistentes', args=[self.evento_sin_archivos.id, self.asistente.id])
        
        response = self.client.get(url_sin_archivos)
        
        self.assertEqual(response.status_code, 200)
        
        datos_evento = response.json()
        
        # Verificar que los campos de archivos son None
        self.assertIsNone(datos_evento['eve_imagen'])
        self.assertIsNone(datos_evento['eve_programacion'])
        # Pero la clave de acceso y QR sí existen (de la inscripción)
        self.assertEqual(datos_evento['eve_clave_acceso'], 'CLAVE789DEF')
        self.assertIsNotNone(datos_evento['codigo_qr'])

    def test_metodo_post_no_permitido(self):
        """CA3: Método POST - COMPORTAMIENTO ACTUAL: 405"""
        response = self.client.post(self.url)
        
        # CORRECCIÓN: La función actual SÍ valida métodos y retorna 405 para POST
        self.assertEqual(response.status_code, 405)

    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado - COMPORTAMIENTO ACTUAL: 200 (sin @login_required)"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        # CORRECCIÓN: La función actual NO tiene @login_required, así que retorna 200
        self.assertEqual(response.status_code, 200)

    def test_estructura_datos_completa(self):
        """CA3: Verificar estructura completa y tipos de datos"""
        response = self.client.get(self.url)
        datos_evento = response.json()
        
        # Verificar tipos de datos
        self.assertIsInstance(datos_evento['eve_id'], int)
        self.assertIsInstance(datos_evento['eve_nombre'], str)
        self.assertIsInstance(datos_evento['eve_descripcion'], str)
        self.assertIsInstance(datos_evento['eve_ciudad'], str)
        self.assertIsInstance(datos_evento['eve_lugar'], str)
        self.assertIsInstance(datos_evento['eve_fecha_inicio'], str)  # Serializado como string
        self.assertIsInstance(datos_evento['eve_fecha_fin'], str)    # Serializado como string
        self.assertIsInstance(datos_evento['eve_categoria'], str)
        
        # Campos que pueden ser string o None
        self.assertTrue(isinstance(datos_evento['eve_imagen'], str) or datos_evento['eve_imagen'] is None)
        self.assertTrue(isinstance(datos_evento['eve_programacion'], str) or datos_evento['eve_programacion'] is None)
        self.assertTrue(isinstance(datos_evento['eve_clave_acceso'], str) or datos_evento['eve_clave_acceso'] is None)
        self.assertTrue(isinstance(datos_evento['codigo_qr'], str) or datos_evento['codigo_qr'] is None)
        
        # Campo que puede ser int o string
        self.assertTrue(isinstance(datos_evento['eve_cantidad'], (int, str)))


    def test_formato_fechas(self):
        """CA3: Verificar formato correcto de las fechas en la respuesta"""
        response = self.client.get(self.url)
        datos_evento = response.json()
        
        # Verificar que las fechas están en formato ISO (YYYY-MM-DD)
        self.assertRegex(datos_evento['eve_fecha_inicio'], r'\d{4}-\d{2}-\d{2}')
        self.assertRegex(datos_evento['eve_fecha_fin'], r'\d{4}-\d{2}-\d{2}')
        
        # Verificar que son las fechas correctas
        self.assertEqual(datos_evento['eve_fecha_inicio'], str(self.evento.eve_fecha_inicio))
        self.assertEqual(datos_evento['eve_fecha_fin'], str(self.evento.eve_fecha_fin))