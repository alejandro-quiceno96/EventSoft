import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from app_eventos.models import Eventos
from app_administrador.models import Administradores

User = get_user_model()

class CancelarEventoTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # Crear administrador de eventos
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='testpass123'
        )
        
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo'
        )
        
        # Crear eventos con diferentes estados para testing
        hoy = timezone.now().date()
        
        # Evento activo para cancelar
        self.evento_activo = Eventos.objects.create(
            eve_nombre='Evento Activo para Cancelar',
            eve_descripcion='Evento que será cancelado manualmente',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen='evento_activo.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Evento pendiente para cancelar
        self.evento_pendiente = Eventos.objects.create(
            eve_nombre='Evento Pendiente',
            eve_descripcion='Evento pendiente que será cancelado',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='pendiente',
            eve_imagen='evento_pendiente.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Evento ya cancelado
        self.evento_cancelado = Eventos.objects.create(
            eve_nombre='Evento Ya Cancelado',
            eve_descripcion='Evento que ya está cancelado',
            eve_ciudad='Cali',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio=hoy + timedelta(days=5),
            eve_fecha_fin=hoy + timedelta(days=6),
            eve_estado='cancelado',
            eve_imagen='evento_cancelado.jpg',
            eve_capacidad=80,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Evento inactivo
        self.evento_inactivo = Eventos.objects.create(
            eve_nombre='Evento Inactivo',
            eve_descripcion='Evento inactivo que será cancelado',
            eve_ciudad='Barranquilla',
            eve_lugar='Lugar Z',
            eve_fecha_inicio=hoy - timedelta(days=10),
            eve_fecha_fin=hoy - timedelta(days=8),
            eve_estado='inactivo',
            eve_imagen='evento_inactivo.jpg',
            eve_capacidad=120,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def test_cancelar_evento_activo(self):
        """CA1: Cancelación exitosa de un evento activo"""
        # Verificar estado inicial
        self.assertEqual(self.evento_activo.eve_estado, 'activo')
        
        # Realizar solicitud para cancelar evento
        url = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se redirige con el parámetro GET correcto
        self.assertIn('modal_cancelar_evento=true', response.url)
        self.assertIn(reverse('super_admin:index_super_admin'), response.url)
        
        # Verificar que el estado del evento cambió en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento_activo.id)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')
    
    def test_cancelar_evento_pendiente(self):
        """CA1: Cancelación exitosa de un evento pendiente"""
        # Verificar estado inicial
        self.assertEqual(self.evento_pendiente.eve_estado, 'pendiente')
        
        url = reverse('super_admin:cancelar_evento', args=[self.evento_pendiente.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_cancelar_evento=true', response.url)
        
        # Verificar que el estado cambió a "Cancelado"
        evento_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')
    
    def test_cancelar_evento_inactivo(self):
        """CA1: Cancelación exitosa de un evento inactivo"""
        # Verificar estado inicial
        self.assertEqual(self.evento_inactivo.eve_estado, 'inactivo')
        
        url = reverse('super_admin:cancelar_evento', args=[self.evento_inactivo.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_cancelar_evento=true', response.url)
        
        # Verificar que el estado cambió a "Cancelado"
        evento_actualizado = Eventos.objects.get(id=self.evento_inactivo.id)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')
    
    def test_cancelar_evento_ya_cancelado(self):
        """CA1: Re-cancelación de un evento ya cancelado"""
        # Verificar estado inicial
        self.assertEqual(self.evento_cancelado.eve_estado, 'cancelado')
        
        url = reverse('super_admin:cancelar_evento', args=[self.evento_cancelado.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_cancelar_evento=true', response.url)
        
        # Verificar que el estado se mantiene como "Cancelado" (con C mayúscula)
        evento_actualizado = Eventos.objects.get(id=self.evento_cancelado.id)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')
    
    def test_evento_no_existe(self):
        """CA2: Manejo de error cuando el evento no existe"""
        evento_id_inexistente = 9999
        
        url = reverse('super_admin:cancelar_evento', args=[evento_id_inexistente])
        response = self.client.get(url)
        
        # Verificar que retorna 404
        self.assertEqual(response.status_code, 404)
    
    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        
        url = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        response = client_no_auth.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    
    def test_informacion_evento_se_mantiene_intacta(self):
        """CA1: Al cancelar, la demás información del evento se mantiene igual"""
        # Capturar información original del evento
        nombre_original = self.evento_activo.eve_nombre
        descripcion_original = self.evento_activo.eve_descripcion
        capacidad_original = self.evento_activo.eve_capacidad
        administrador_original = self.evento_activo.eve_administrador_fk
        
        # Cancelar el evento
        url = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        self.client.get(url)
        
        # Verificar que la información se mantiene (solo cambia el estado)
        evento_actualizado = Eventos.objects.get(id=self.evento_activo.id)
        self.assertEqual(evento_actualizado.eve_nombre, nombre_original)
        self.assertEqual(evento_actualizado.eve_descripcion, descripcion_original)
        self.assertEqual(evento_actualizado.eve_capacidad, capacidad_original)
        self.assertEqual(evento_actualizado.eve_administrador_fk, administrador_original)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')  # Solo esto cambió
    
    def test_cancelacion_multiples_eventos(self):
        """CA1: Cancelación secuencial de múltiples eventos"""
        # Verificar estados iniciales
        self.assertEqual(self.evento_activo.eve_estado, 'activo')
        self.assertEqual(self.evento_pendiente.eve_estado, 'pendiente')
        
        # Cancelar primer evento
        url1 = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        response1 = self.client.get(url1)
        self.assertEqual(response1.status_code, 302)
        
        # Cancelar segundo evento
        url2 = reverse('super_admin:cancelar_evento', args=[self.evento_pendiente.id])
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 302)
        
        # Verificar que ambos eventos están cancelados
        evento1_actualizado = Eventos.objects.get(id=self.evento_activo.id)
        evento2_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        
        self.assertEqual(evento1_actualizado.eve_estado, 'Cancelado')
        self.assertEqual(evento2_actualizado.eve_estado, 'Cancelado')
    
    def test_estado_exacto_cancelado(self):
        """CA1: Verificar que el estado se establece exactamente como 'Cancelado' (con C mayúscula)"""
        url = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        self.client.get(url)
        
        evento_actualizado = Eventos.objects.get(id=self.evento_activo.id)
        
        # Verificar el estado exacto (importante para consistencia)
        self.assertEqual(evento_actualizado.eve_estado, 'Cancelado')
        self.assertNotEqual(evento_actualizado.eve_estado, 'cancelado')  # No debe ser minúscula
    
    def test_metodos_http_no_permitidos(self):
        """Verificar que solo el método GET está permitido"""
        # Probar POST
        url = reverse('super_admin:cancelar_evento', args=[self.evento_activo.id])
        response_post = self.client.post(url)
        # Debería redirigir igual o manejar el error apropiadamente
        self.assertIn(response_post.status_code, [302, 405])
        
        # Probar PUT
        response_put = self.client.put(url)
        self.assertIn(response_put.status_code, [302, 405])
        
        # Probar DELETE
        response_delete = self.client.delete(url)
        self.assertIn(response_delete.status_code, [302, 405])