import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from app_eventos.models import Eventos
from app_administrador.models import Administradores

User = get_user_model()

class EliminarEventoTestCase(TestCase):
    
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
        
        # Crear eventos con diferentes estados y fechas para testing
        hoy = timezone.now().date()
        
        # Evento activo futuro
        self.evento_activo_futuro = Eventos.objects.create(
            eve_nombre='Evento Activo Futuro',
            eve_descripcion='Evento activo que ocurrirá en el futuro',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen='evento_futuro.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Evento que ya pasó (para depuración del sitio web)
        self.evento_pasado = Eventos.objects.create(
            eve_nombre='Evento que Ya Pasó',
            eve_descripcion='Evento que ya finalizó',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy - timedelta(days=30),
            eve_fecha_fin=hoy - timedelta(days=28),
            eve_estado='inactivo',
            eve_imagen='evento_pasado.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Evento cancelado
        self.evento_cancelado = Eventos.objects.create(
            eve_nombre='Evento Cancelado',
            eve_descripcion='Evento que fue cancelado',
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
        
        # Evento pendiente
        self.evento_pendiente = Eventos.objects.create(
            eve_nombre='Evento Pendiente',
            eve_descripcion='Evento pendiente de aprobación',
            eve_ciudad='Barranquilla',
            eve_lugar='Lugar Z',
            eve_fecha_inicio=hoy + timedelta(days=20),
            eve_fecha_fin=hoy + timedelta(days=22),
            eve_estado='pendiente',
            eve_imagen='evento_pendiente.jpg',
            eve_capacidad=120,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Contar eventos iniciales
        self.total_eventos_inicial = Eventos.objects.count()
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def test_eliminar_evento_pasado(self):
        """CA1: Eliminación exitosa de un evento que ya pasó (caso principal HU96)"""
        # Verificar que el evento existe antes de eliminar
        self.assertTrue(Eventos.objects.filter(id=self.evento_pasado.id).exists())
        
        # Realizar solicitud para eliminar evento
        url = reverse('super_admin:eliminar_evento', args=[self.evento_pasado.id])
        response = self.client.get(url)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se redirige con el parámetro GET correcto
        self.assertIn('modal_eliminado_evento=true', response.url)
        self.assertIn(reverse('super_admin:index_super_admin'), response.url)
        
        # Verificar que el evento fue eliminado de la base de datos
        self.assertFalse(Eventos.objects.filter(id=self.evento_pasado.id).exists())
        
        # Verificar que el contador de eventos disminuyó
        self.assertEqual(Eventos.objects.count(), self.total_eventos_inicial - 1)
    
    def test_eliminar_evento_activo_futuro(self):
        """CA1: Eliminación exitosa de un evento activo futuro"""
        # Verificar que el evento existe antes de eliminar
        self.assertTrue(Eventos.objects.filter(id=self.evento_activo_futuro.id).exists())
        
        url = reverse('super_admin:eliminar_evento', args=[self.evento_activo_futuro.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_eliminado_evento=true', response.url)
        
        # Verificar que el evento fue eliminado
        self.assertFalse(Eventos.objects.filter(id=self.evento_activo_futuro.id).exists())
        self.assertEqual(Eventos.objects.count(), self.total_eventos_inicial - 1)
    
    def test_eliminar_evento_cancelado(self):
        """CA1: Eliminación exitosa de un evento cancelado"""
        self.assertTrue(Eventos.objects.filter(id=self.evento_cancelado.id).exists())
        
        url = reverse('super_admin:eliminar_evento', args=[self.evento_cancelado.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_eliminado_evento=true', response.url)
        
        self.assertFalse(Eventos.objects.filter(id=self.evento_cancelado.id).exists())
        self.assertEqual(Eventos.objects.count(), self.total_eventos_inicial - 1)
    
    def test_eliminar_evento_pendiente(self):
        """CA1: Eliminación exitosa de un evento pendiente"""
        self.assertTrue(Eventos.objects.filter(id=self.evento_pendiente.id).exists())
        
        url = reverse('super_admin:eliminar_evento', args=[self.evento_pendiente.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_eliminado_evento=true', response.url)
        
        self.assertFalse(Eventos.objects.filter(id=self.evento_pendiente.id).exists())
        self.assertEqual(Eventos.objects.count(), self.total_eventos_inicial - 1)
    
    def test_evento_no_existe(self):
        """CA2: Manejo de error cuando el evento no existe"""
        evento_id_inexistente = 9999
        
        url = reverse('super_admin:eliminar_evento', args=[evento_id_inexistente])
        response = self.client.get(url)
        
        # Verificar que retorna 404
        self.assertEqual(response.status_code, 404)
        
        # Verificar que no se eliminó ningún evento
        self.assertEqual(Eventos.objects.count(), self.total_eventos_inicial)
    
    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        
        url = reverse('super_admin:eliminar_evento', args=[self.evento_pasado.id])
        response = client_no_auth.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Verificar que el evento NO fue eliminado
        self.assertTrue(Eventos.objects.filter(id=self.evento_pasado.id).exists())
    
    
    def test_eliminacion_permanente(self):
        """CA1: Verificar que la eliminación es permanente (no soft delete)"""
        # Capturar información del evento antes de eliminar
        evento_id = self.evento_pasado.id
        evento_nombre = self.evento_pasado.eve_nombre
        
        # Eliminar el evento
        url = reverse('super_admin:eliminar_evento', args=[evento_id])
        self.client.get(url)
        
        # Verificar que el evento no existe en absoluto en la base de datos
        with self.assertRaises(Eventos.DoesNotExist):
            Eventos.objects.get(id=evento_id)
        
        # Verificar que no existe por ningún campo
        self.assertFalse(Eventos.objects.filter(eve_nombre=evento_nombre).exists())
    
    def test_eliminacion_multiples_eventos(self):
        """CA1: Eliminación secuencial de múltiples eventos"""
        # Verificar cantidad inicial
        self.assertEqual(Eventos.objects.count(), 4)
        
        # Eliminar primer evento
        url1 = reverse('super_admin:eliminar_evento', args=[self.evento_pasado.id])
        response1 = self.client.get(url1)
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(Eventos.objects.count(), 3)
        
        # Eliminar segundo evento
        url2 = reverse('super_admin:eliminar_evento', args=[self.evento_cancelado.id])
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(Eventos.objects.count(), 2)
        
        # Eliminar tercer evento
        url3 = reverse('super_admin:eliminar_evento', args=[self.evento_pendiente.id])
        response3 = self.client.get(url3)
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(Eventos.objects.count(), 1)
    
    def test_integridad_referencial(self):
        """CA1: Verificar que la eliminación no afecta otros modelos relacionados"""
        # Este test verifica que al eliminar un evento, no hay problemas de integridad referencial
        # En un caso real, podrías necesitar verificar relaciones con otros modelos
        
        # Contar eventos relacionados con el mismo administrador antes de eliminar
        eventos_del_administrador_antes = Eventos.objects.filter(
            eve_administrador_fk=self.administrador
        ).count()
        
        # Eliminar un evento
        url = reverse('super_admin:eliminar_evento', args=[self.evento_pasado.id])
        self.client.get(url)
        
        # Verificar que el administrador sigue existiendo
        self.assertTrue(Administradores.objects.filter(id=self.administrador.id).exists())
        
        # Verificar que los otros eventos del mismo administrador siguen existiendo
        eventos_del_administrador_despues = Eventos.objects.filter(
            eve_administrador_fk=self.administrador
        ).count()
        
        self.assertEqual(eventos_del_administrador_despues, eventos_del_administrador_antes - 1)
    
    def test_eliminacion_todos_los_estados(self):
        """CA1: La función puede eliminar eventos en cualquier estado"""
        estados_eliminados = []
        
        # Eliminar eventos en diferentes estados
        eventos_a_eliminar = [
            self.evento_activo_futuro,  # activo
            self.evento_pendiente,      # pendiente  
            self.evento_cancelado,      # cancelado
            self.evento_pasado          # inactivo
        ]
        
        for evento in eventos_a_eliminar:
            with self.subTest(estado=evento.eve_estado):
                # Verificar que existe antes
                self.assertTrue(Eventos.objects.filter(id=evento.id).exists())
                
                # Eliminar
                url = reverse('super_admin:eliminar_evento', args=[evento.id])
                response = self.client.get(url)
                
                # Verificar éxito
                self.assertEqual(response.status_code, 302)
                self.assertIn('modal_eliminado_evento=true', response.url)
                
                # Verificar que fue eliminado
                self.assertFalse(Eventos.objects.filter(id=evento.id).exists())
                
                estados_eliminados.append(evento.eve_estado)
        
        # Verificar que se eliminaron eventos de todos los estados
        self.assertEqual(len(estados_eliminados), 4)
        self.assertIn('activo', estados_eliminados)
        self.assertIn('pendiente', estados_eliminados)
        self.assertIn('cancelado', estados_eliminados)
        self.assertIn('inactivo', estados_eliminados)
    