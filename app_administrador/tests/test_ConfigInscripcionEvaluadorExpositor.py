import json
from django.test import TestCase, Client
from django.urls import reverse
from app_administrador.models import Administradores 
from app_eventos.models import Eventos 
from app_usuarios.models import Usuario as User

class ConfigInscripcionTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_test',
            password='testpass123',
            email='admin@test.com'
        )
        
        # Crear administrador para la relación ForeignKey
        self.administrador = Administradores.objects.create(
            usuario=self.user,
        )
        
        # Crear un evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Test",
            eve_descripcion="Descripción del evento test",
            eve_ciudad="Ciudad Test",
            eve_lugar="Lugar Test",
            eve_fecha_inicio="2024-01-01",
            eve_fecha_fin="2024-01-02",
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_habilitar_participantes=True,  # Valor inicial
            eve_habilitar_evaluadores=False   # Valor inicial
        )
        
        self.url = reverse('administrador:configurar_inscripcion', args=[self.evento.id])
    
    def test_acceso_sin_autenticar(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirección a login
        self.assertIn('login', response.url)
    
    def test_metodo_get_no_permitido(self):
        """CA1: Método GET retorna error 405"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Método no permitido")
    
    def test_actualizar_evaluadores_activo(self):
        """CA2: Actualizar evaluadores a activo (estado=1)"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Estado inicial debe ser False
        self.assertFalse(self.evento.eve_habilitar_evaluadores)
        
        data = {
            "estado": 1,
            "tipo": "Evaluador"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta JSON
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], "Evaluador actualizado a 1")
        
        # Verificar que se actualizó en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertTrue(evento_actualizado.eve_habilitar_evaluadores)
        # Verificar que no se modificó el campo de participantes
        self.assertTrue(evento_actualizado.eve_habilitar_participantes)
    
    def test_actualizar_evaluadores_inactivo(self):
        """CA2: Actualizar evaluadores a inactivo (estado=0)"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Primero activamos para luego desactivar
        self.evento.eve_habilitar_evaluadores = True
        self.evento.save()
        
        data = {
            "estado": 0,
            "tipo": "Evaluador"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que se desactivó en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertFalse(evento_actualizado.eve_habilitar_evaluadores)
    
    def test_actualizar_expositores_activo(self):
        """CA2: Actualizar expositores a activo (estado=1)"""
        self.client.login(username='admin_test', password='testpass123')
        
        data = {
            "estado": 1,
            "tipo": "Expositor"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que se activó en la base de datos (ya estaba True, pero se confirma)
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertTrue(evento_actualizado.eve_habilitar_participantes)
        # Verificar que no se modificó el campo de evaluadores
        self.assertFalse(evento_actualizado.eve_habilitar_evaluadores)
    
    def test_actualizar_expositores_inactivo(self):
        """CA2: Actualizar expositores a inactivo (estado=0)"""
        self.client.login(username='admin_test', password='testpass123')
        
        data = {
            "estado": 0,
            "tipo": "Expositor"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], "Expositor actualizado a 0")
        
        # Verificar que se desactivó en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertFalse(evento_actualizado.eve_habilitar_participantes)
    
    def test_tipo_invalido(self):
        """CA3: Tipo inválido no actualiza ningún campo"""
        self.client.login(username='admin_test', password='testpass123')
        
        estado_original_eval = self.evento.eve_habilitar_evaluadores
        estado_original_expo = self.evento.eve_habilitar_participantes
        
        data = {
            "estado": 1,
            "tipo": "TipoInvalido"
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verificar que no hubo cambios en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento.id)
        self.assertEqual(evento_actualizado.eve_habilitar_evaluadores, estado_original_eval)
        self.assertEqual(evento_actualizado.eve_habilitar_participantes, estado_original_expo)
        
        # La vista aún retorna éxito porque no hay validación de tipos
        # Esto podría considerarse un issue a mejorar
    
    def test_evento_no_existente(self):
        """CA3: Evento que no existe retorna error 404"""
        self.client.login(username='admin_test', password='testpass123')
        
        url_invalida = reverse('administrador:configurar_inscripcion', args=[999])  # ID que no existe
        
        data = {
            "estado": 1,
            "tipo": "Evaluador"
        }
        
        response = self.client.post(
            url_invalida,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    