from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, EvaluadoresEventos, Proyecto
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from app_evaluador.models import Evaluadores, EvaluadorProyecto
import json


class DesignarEvaluadorAjaxTestCase(TestCase):
    
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
            eve_nombre='Evento Test Designación',
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
            pro_nombre='Proyecto Test Designación',
            pro_descripcion='Descripción del proyecto test',
            pro_documentos=SimpleUploadedFile("proyecto.pdf", b"file_content"),
            pro_estado='En revisión',
            pro_calificación_final=None
        )
        
        # Crear evaluadores
        self.evaluador_asignado_user = User.objects.create_user(
            username='evaluador_asignado',
            email='asignado@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='11111111',
            first_name='Carlos',
            last_name='Asignado'
        )
        
        self.evaluador_no_asignado_user = User.objects.create_user(
            username='evaluador_no_asignado',
            email='noasignado@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='22222222',
            first_name='Laura',
            last_name='No Asignada'
        )
        
        self.evaluador_asignado = Evaluadores.objects.create(usuario=self.evaluador_asignado_user)
        self.evaluador_no_asignado = Evaluadores.objects.create(usuario=self.evaluador_no_asignado_user)
        
        # Crear relaciones evaluador-evento
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador_asignado,
            eva_eve_evento_fk=self.evento,
            eva_estado='Admitido',
            eva_eve_areas_interes='Tecnología'
        )
        
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador_no_asignado,
            eva_eve_evento_fk=self.evento,
            eva_estado='Admitido',
            eva_eve_areas_interes='Ciencias'
        )
        
        # Crear asignación previa para un evaluador
        EvaluadorProyecto.objects.create(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador_asignado
        )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador_asignado.id])
        
        response = self.client.post(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_metodo_get_no_permitido(self):
        """Prueba que GET retorne método no permitido"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador_asignado.id])
        
        response = self.client.get(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Método no permitido.')

    def test_designar_evaluador_exitoso(self):
        """Prueba que se pueda eliminar la asignación de un evaluador exitosamente"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador_asignado.id])
        
        # Verificar que está asignado inicialmente
        asignacion_existente = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador_asignado
        ).exists()
        self.assertTrue(asignacion_existente)
        
        # Realizar designación (eliminación)
        response = self.client.post(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Asignaciónn cancelada correctamente.')
        
        # Verificar que se eliminó la asignación en la base de datos
        asignacion_eliminada = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador_asignado
        ).exists()
        self.assertFalse(asignacion_eliminada)

    def test_designar_evaluador_sin_asignacion_previa(self):
        """Prueba designar un evaluador que no tenía asignación previa"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, self.evaluador_no_asignado.id])
        
        # Verificar que no está asignado inicialmente
        asignacion_existente = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador_no_asignado
        ).exists()
        self.assertFalse(asignacion_existente)
        
        # Realizar designación (aunque no exista asignación)
        response = self.client.post(url)
        
        # Verificar respuesta exitosa (delete() no falla si no existe)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Asignaciónn cancelada correctamente.')
        
        # Verificar que sigue sin asignación
        asignacion_eliminada = EvaluadorProyecto.objects.filter(
            eva_pro_proyecto_fk=self.proyecto,
            eva_pro_evaluador_fk=self.evaluador_no_asignado
        ).exists()
        self.assertFalse(asignacion_eliminada)

    def test_evento_no_existente(self):
        """Prueba el comportamiento con un ID de evento que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[99999, self.proyecto.id, self.evaluador_asignado.id])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_proyecto_no_existente(self):
        """Prueba el comportamiento con un ID de proyecto que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, 99999, self.evaluador_asignado.id])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_evaluador_no_existente(self):
        """Prueba el comportamiento con un ID de evaluador que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:designar_evaluador', 
                     args=[self.evento.id, self.proyecto.id, 99999])
        
        response = self.client.post(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

