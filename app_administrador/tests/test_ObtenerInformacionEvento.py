from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, EventosCategorias,  ParticipantesEventos, AsistentesEventos
from app_categorias.models import Categorias
from app_areas.models import Areas
from app_certificados.models import Certificado
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
import json


class ObtenerEventoTestCase(TestCase):
    
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
        
        # Crear área y categoría
        self.area = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología'
        )
        
        self.categoria = Categorias.objects.create(
            cat_nombre='Desarrollo Web',
            cat_area_fk=self.area
        )
        
        # Crear archivos de prueba
        self.imagen_evento = SimpleUploadedFile(
            "evento.jpg", 
            b"contenido_imagen", 
            content_type="image/jpeg"
        )
        
        self.programacion_evento = SimpleUploadedFile(
            "programacion.pdf", 
            b"contenido_pdf", 
            content_type="application/pdf"
        )
        
        self.ficha_tecnica = SimpleUploadedFile(
            "ficha_tecnica.pdf", 
            b"contenido_ficha", 
            content_type="application/pdf"
        )
        
        # Crear evento completo
        self.evento_completo = Eventos.objects.create(
            eve_nombre='Evento Completo 2024',
            eve_descripcion='Descripción completa del evento',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_imagen=self.imagen_evento,
            eve_capacidad=150,
            eve_tienecosto=True,
            eve_programacion=self.programacion_evento,
            eve_memorias='https://drive.google.com/memorias',
            eve_informacion_tecnica=self.ficha_tecnica,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=False,
            eve_administrador_fk=self.administrador,
        )
        
        # Asignar categoría al evento
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_completo,
            eve_cat_categoria_fk=self.categoria
        )
        
        # Crear certificado para el evento
        Certificado.objects.create(
            evento_fk=self.evento_completo,
            firma_nombre='Director General',
            firma_cargo='Director'
        )
        
        # Crear evento mínimo (sin archivos ni extras)
        self.evento_minimo = Eventos.objects.create(
            eve_nombre='Evento Mínimo',
            eve_descripcion='Evento con datos mínimos',
            eve_ciudad='Medellín',
            eve_lugar='Auditorio Secundario',
            eve_fecha_inicio='2024-02-01',
            eve_fecha_fin='2024-02-02',
            eve_estado='Pendiente',
            eve_capacidad=0,  # Sin capacidad definida
            eve_tienecosto=False,
            eve_habilitar_participantes=False,
            eve_habilitar_evaluadores=True,
            eve_administrador_fk=self.administrador
        )
        
        # Asignar categoría al evento mínimo
        EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento_minimo,
            eve_cat_categoria_fk=self.categoria
        )

    def test_obtener_evento_existente_completo(self):
        """Prueba obtener un evento existente con todos los datos"""
        url = reverse('administrador:evento_detalle', args=[self.evento_completo.id])
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Verificar estructura de datos
        data = response.json()
        
        # Verificar datos básicos del evento
        self.assertEqual(data['eve_id'], self.evento_completo.id)
        self.assertEqual(data['eve_nombre'], 'Evento Completo 2024')
        self.assertEqual(data['eve_descripcion'], 'Descripción completa del evento')
        self.assertEqual(data['eve_ciudad'], 'Bogotá')
        self.assertEqual(data['eve_lugar'], 'Auditorio Principal')
        self.assertEqual(data['eve_estado'], 'Activo')
        self.assertEqual(data['eve_categoria'], 'Desarrollo Web')
        self.assertEqual(data['eve_cantidad'], 150)
        self.assertEqual(data['eve_costo'], 'Con Pago')
        
        # Verificar URLs de archivos
        self.assertIsNotNone(data['eve_imagen'])
        self.assertIsNotNone(data['eve_programacion'])
        self.assertIsNotNone(data['ficha_tecnica'])
        
        # Verificar fechas formateadas
        self.assertEqual(data['eve_fecha_inicio'], '2024-01-01')
        self.assertEqual(data['eve_fecha_fin'], '2024-01-02')
        
        # Verificar memorias y certificado
        self.assertEqual(data['memorias'], 'https://drive.google.com/memorias')
        self.assertTrue(data['certificado'])
        
        # Verificar configuraciones de inscripción
        self.assertTrue(data['inscripcion_expositor'])
        self.assertFalse(data['inscripcion_evaluador'])

    def test_obtener_evento_minimo(self):
        """Prueba obtener un evento con datos mínimos"""
        url = reverse('administrador:evento_detalle', args=[self.evento_minimo.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Verificar datos básicos
        self.assertEqual(data['eve_id'], self.evento_minimo.id)
        self.assertEqual(data['eve_nombre'], 'Evento Mínimo')
        self.assertEqual(data['eve_costo'], 'Sin Pago')
        
        # Verificar valores por defecto para campos opcionales
        self.assertIsNone(data['eve_imagen'])
        self.assertIsNone(data['eve_programacion'])
        self.assertFalse(data['ficha_tecnica'])
        self.assertFalse(data['memorias'])
        self.assertFalse(data['certificado'])
        
        # Verificar configuraciones de inscripción
        self.assertFalse(data['inscripcion_expositor'])
        self.assertTrue(data['inscripcion_evaluador'])

    def test_obtener_evento_no_existente(self):
        """Prueba obtener un evento que no existe"""
        url = reverse('administrador:evento_detalle', args=[99999])  # ID que no existe
        
        response = self.client.get(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_metodo_post_no_permitido(self):
        """Prueba que POST retorne método no permitido"""
        url = reverse('administrador:evento_detalle', args=[self.evento_completo.id])
        
        response = self.client.post(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_estructura_datos_completa(self):
        """Prueba que la estructura de datos incluya todos los campos esperados"""
        url = reverse('administrador:evento_detalle', args=[self.evento_completo.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Lista de campos esperados
        campos_esperados = [
            'eve_id', 'eve_nombre', 'eve_descripcion', 'eve_ciudad', 'eve_lugar',
            'eve_fecha_inicio', 'eve_fecha_fin', 'eve_estado', 'eve_imagen',
            'eve_cantidad', 'eve_costo', 'eve_programacion', 'eve_categoria',
            'cantidad_participantes', 'cantidad_asistentes', 'memorias',
            'certificado', 'ficha_tecnica', 'inscripcion_expositor', 'inscripcion_evaluador'
        ]
        
        # Verificar que todos los campos están presentes
        for campo in campos_esperados:
            self.assertIn(campo, data)

    def test_evento_sin_categoria(self):
        """Prueba obtener un evento sin categoría asignada"""
        # Crear evento sin categoría
        evento_sin_categoria = Eventos.objects.create(
            eve_nombre='Evento Sin Categoría',
            eve_descripcion='Evento sin categoría',
            eve_ciudad='Cali',
            eve_lugar='Auditorio',
            eve_fecha_inicio='2024-03-01',
            eve_fecha_fin='2024-03-02',
            eve_estado='Activo',
            eve_capacidad=50,
            eve_administrador_fk=self.administrador
        )
        
        url = reverse('administrador:evento_detalle', args=[evento_sin_categoria.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Verificar que la categoría está vacía
        self.assertEqual(data['eve_categoria'], '')

