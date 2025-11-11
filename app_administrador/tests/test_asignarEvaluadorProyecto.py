from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, EvaluadoresEventos, Proyecto
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from app_evaluador.models import Evaluadores,  EvaluadorProyecto
from unittest.mock import patch
import json


class AsignarEvaluadorAjaxTestCase(TestCase):
    
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
        
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test Asignación',
            eve_descripcion='Descripción del evento test',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear proyecto
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo='PROY001',
            pro_nombre='Proyecto Test Asignación',
            pro_descripcion='Descripción del proyecto test',
            pro_documentos=SimpleUploadedFile("proyecto.pdf", b"file_content"),
            pro_estado='En revisión',
            pro_calificación_final=None
        )
        
        # Crear evaluador
        self.evaluador_user = User.objects.create_user(
            username='evaluador_test',
            email='evaluador@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='11111111',
            first_name='Carlos',
            last_name='Evaluador'
        )
        
        self.evaluador = Evaluadores.objects.create(usuario=self.evaluador_user)
        
        # Crear relación evaluador-evento
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador,
            eva_eve_evento_fk=self.evento,
            eva_estado='Admitido',
            eva_eve_areas_interes='Tecnología'
        )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        
        response = self.client.post(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_metodo_get_no_permitido(self):
        """Prueba que GET retorne método no permitido"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        
        response = self.client.get(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Método no permitido.')

    def test_asignar_evaluador_exitoso(self):
        """Prueba que se pueda asignar un evaluador a un proyecto exitosamente"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        
        # Verificar que no está asignado inicialmente
        asignacion_existente = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador
        ).exists()
        self.assertFalse(asignacion_existente)
        
        # Realizar asignación
        response = self.client.post(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Evaluador asignado y notificado por correo.')
        
        # Verificar que se creó la asignación en la base de datos
        asignacion_creada = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador
        ).exists()
        self.assertTrue(asignacion_creada)

    def test_evaluador_ya_asignado(self):
        """Prueba que no se pueda asignar un evaluador que ya está asignado"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        
        # Crear asignación previa
        EvaluadorProyecto.objects.create(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador
        )
        
        # Intentar asignar nuevamente
        response = self.client.post(url)
        
        # Verificar respuesta de error
        self.assertEqual(response.status_code, 200)  # Aunque es error, retorna 200
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Este evaluador ya está asignado al proyecto.')
        
        # Verificar que no se duplicó la asignación
        asignaciones_count = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador
        ).count()
        self.assertEqual(asignaciones_count, 1)

    def test_evaluador_sin_email(self):
        """Prueba asignación de evaluador sin email"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Crear evaluador sin email
        evaluador_sin_email_user = User.objects.create_user(
            username='evaluador_sin_email',
            email='',  # Email vacío
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='22222222',
            first_name='Evaluador',
            last_name='Sin Email'
        )
        
        evaluador_sin_email = Evaluadores.objects.create(usuario=evaluador_sin_email_user)
        
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=evaluador_sin_email,
            eva_eve_evento_fk=self.evento,
            eva_estado='Admitido',
            eva_eve_areas_interes='Ciencias'
        )
        
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, evaluador_sin_email.id])
        
        response = self.client.post(url)
        
        # Verificar que la asignación fue exitosa a pesar de no tener email
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verificar que no se envió correo
        self.assertEqual(len(mail.outbox), 0)

    def test_evento_no_existente(self):
        """Prueba el comportamiento con un ID de evento que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[99999, self.proyecto.id, self.evaluador.id])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_proyecto_no_existente(self):
        """Prueba el comportamiento con un ID de proyecto que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, 99999, self.evaluador.id])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_evaluador_no_existente(self):
        """Prueba el comportamiento con un ID de evaluador que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:asignar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, 99999])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

