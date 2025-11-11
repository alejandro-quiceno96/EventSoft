from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app_eventos.models import Eventos, Proyecto,EvaluadoresEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from app_evaluador.models import Evaluadores,  EvaluadorProyecto
import json


class ListarEvaluadoresAjaxTestCase(TestCase):
    
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
            eve_nombre='Evento Test Evaluadores',
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
            pro_nombre='Proyecto Test',
            pro_descripcion='Descripción del proyecto test',
            pro_documentos=None,
            pro_estado='En revisión',
            pro_calificación_final=None
        )
        
        # Crear evaluadores
        self.evaluadores_data = [
            {
                'username': 'evaluador1',
                'email': 'evaluador1@test.com',
                'documento': '11111111',
                'first_name': 'Carlos',
                'last_name': 'Hernández',
                'estado': 'Admitido',
                'area': 'Tecnología'
            },
            {
                'username': 'evaluador2', 
                'email': 'evaluador2@test.com',
                'documento': '22222222',
                'first_name': 'Laura',
                'last_name': 'Ramírez',
                'estado': 'Admitido',
                'area': 'Ciencias'
            },
            {
                'username': 'evaluador3',
                'email': 'evaluador3@test.com', 
                'documento': '33333333',
                'first_name': 'Miguel',
                'last_name': 'Torres',
                'estado': 'Rechazado',  # Este NO debe aparecer
                'area': 'Artes'
            }
        ]
        
        self.evaluadores_admitidos = []
        for eval_data in self.evaluadores_data:
            # Crear usuario evaluador
            user_evaluador = User.objects.create_user(
                username=eval_data['username'],
                email=eval_data['email'],
                password='testpass123',
                tipo_documento='CC',
                documento_identidad=eval_data['documento'],
                first_name=eval_data['first_name'],
                last_name=eval_data['last_name']
            )
            
            # Crear perfil de evaluador
            evaluador = Evaluadores.objects.create(usuario=user_evaluador)
            
            # Crear relación con evento
            EvaluadoresEventos.objects.create(
                eva_eve_evaluador_fk=evaluador,
                eva_eve_evento_fk=self.evento,
                eva_estado=eval_data['estado'],
                eva_eve_areas_interes=eval_data['area']
            )
            
            if eval_data['estado'] == 'Admitido':
                self.evaluadores_admitidos.append(evaluador)
        
        # Asignar el primer evaluador al proyecto
        if self.evaluadores_admitidos:
            EvaluadorProyecto.objects.create(
                eva_pro_proyecto_fk=self.proyecto,
                eva_pro_evaluador_fk=self.evaluadores_admitidos[0]
            )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_listar_evaluadores_admitidos(self):
        """Prueba que se listen solo los evaluadores admitidos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Verificar contenido JSON
        data = response.json()
        self.assertIn('evaluadores', data)
        
        # Deberían listarse solo 2 evaluadores (los admitidos)
        self.assertEqual(len(data['evaluadores']), 2)
        
        # Verificar que no está el evaluador rechazado
        evaluadores_ids = [e['id'] for e in data['evaluadores']]
        evaluador_rechazado = Evaluadores.objects.get(usuario__username='evaluador3')
        self.assertNotIn(evaluador_rechazado.id, evaluadores_ids)

    def test_estructura_datos_evaluadores(self):
        """Prueba la estructura de datos de los evaluadores"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Verificar estructura de cada evaluador
        for evaluador in data['evaluadores']:
            self.assertIn('id', evaluador)
            self.assertIn('nombre', evaluador)
            self.assertIn('area', evaluador)
            self.assertIn('asignado', evaluador)
            
            # Verificar tipos de datos
            self.assertIsInstance(evaluador['id'], int)
            self.assertIsInstance(evaluador['nombre'], str)
            self.assertIsInstance(evaluador['area'], str)
            self.assertIsInstance(evaluador['asignado'], bool)

    def test_estado_asignacion_evaluadores(self):
        """Prueba que se identifique correctamente qué evaluadores están asignados al proyecto"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Encontrar el evaluador asignado
        evaluador_asignado = None
        evaluador_no_asignado = None
        
        for evaluador in data['evaluadores']:
            if evaluador['asignado']:
                evaluador_asignado = evaluador
            else:
                evaluador_no_asignado = evaluador
        
        # Verificar que hay un evaluador asignado
        self.assertIsNotNone(evaluador_asignado)
        self.assertIsNotNone(evaluador_no_asignado)
        
        # Verificar que el ID del evaluador asignado es correcto
        evaluador_esperado = self.evaluadores_admitidos[0]
        self.assertEqual(evaluador_asignado['id'], evaluador_esperado.id)

    def test_nombres_completos_evaluadores(self):
        """Prueba que los nombres estén en el formato correcto"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Verificar formato de nombres
        for evaluador in data['evaluadores']:
            nombre_completo = evaluador['nombre']
            self.assertIn(' ', nombre_completo)  # Debe tener al menos un espacio
            partes_nombre = nombre_completo.split()
            self.assertGreaterEqual(len(partes_nombre), 2)  # Al menos nombre y apellido

    def test_areas_interes_evaluadores(self):
        """Prueba que las áreas de interés se muestren correctamente"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Verificar áreas de interés
        areas_esperadas = ['Tecnología', 'Ciencias']
        areas_obtenidas = [e['area'] for e in data['evaluadores']]
        
        for area in areas_esperadas:
            self.assertIn(area, areas_obtenidas)

    def test_evento_no_existente(self):
        """Prueba el comportamiento con un ID de evento que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[99999, self.proyecto.id])  # Evento que no existe
        
        response = self.client.get(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)

    def test_proyecto_no_existente(self):
        """Prueba el comportamiento con un ID de proyecto que no existe"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:listar_evaluadores', 
                     args=[self.evento.id, 99999])  # Proyecto que no existe
        
        response = self.client.get(url)
        
        # Debería retornar 404
        self.assertEqual(response.status_code, 404)