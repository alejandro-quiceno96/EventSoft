import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_eventos.models import Eventos
from app_administrador.models import Administradores

User = get_user_model()

class PublicarEventoWebTestCase(TestCase):
    
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
        hoy = datetime.now().date()
        
        # Evento pendiente para publicar
        self.evento_pendiente = Eventos.objects.create(
            eve_nombre='Evento Pendiente para Publicar',
            eve_descripcion='Evento listo para ser publicado en el sitio web',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='pendiente',
            eve_imagen='evento_pendiente.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Evento inactivo para reactivar
        self.evento_inactivo = Eventos.objects.create(
            eve_nombre='Evento Inactivo',
            eve_descripcion='Evento que estaba inactivo',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='inactivo',
            eve_imagen='evento_inactivo.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Evento ya activo
        self.evento_activo = Eventos.objects.create(
            eve_nombre='Evento Ya Activo',
            eve_descripcion='Evento que ya está publicado',
            eve_ciudad='Cali',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio=hoy + timedelta(days=20),
            eve_fecha_fin=hoy + timedelta(days=22),
            eve_estado='activo',
            eve_imagen='evento_activo.jpg',
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def test_publicar_evento_pendiente(self):
        """CA1: Publicación exitosa de un evento pendiente a activo"""
        # Verificar estado inicial
        self.assertEqual(self.evento_pendiente.eve_estado, 'pendiente')
        
        # Realizar solicitud para publicar evento (cambiar a activo)
        url = reverse('super_admin:modificar_eventos', args=[self.evento_pendiente.id, 'activo'])
        response = self.client.get(url)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se redirige con el parámetro GET correcto
        self.assertIn('modal_evento_activo=true', response.url)
        self.assertIn(reverse('super_admin:index_super_admin'), response.url)
        
        # Verificar que el estado del evento cambió en la base de datos
        evento_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        self.assertEqual(evento_actualizado.eve_estado, 'activo')
    
    def test_reactivar_evento_inactivo(self):
        """CA1: Reactivación exitosa de un evento inactivo a activo"""
        # Verificar estado inicial
        self.assertEqual(self.evento_inactivo.eve_estado, 'inactivo')
        
        # Realizar solicitud para reactivar evento
        url = reverse('super_admin:modificar_eventos', args=[self.evento_inactivo.id, 'activo'])
        response = self.client.get(url)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('modal_evento_activo=true', response.url)
        
        # Verificar que el estado del evento cambió
        evento_actualizado = Eventos.objects.get(id=self.evento_inactivo.id)
        self.assertEqual(evento_actualizado.eve_estado, 'activo')
    
    def test_evento_no_existe(self):
        """CA2: Manejo de error cuando el evento no existe"""
        evento_id_inexistente = 9999
        
        url = reverse('super_admin:modificar_eventos', args=[evento_id_inexistente, 'activo'])
        response = self.client.get(url)
        
        # Verificar que retorna 404
        self.assertEqual(response.status_code, 404)
    
  
    def test_cambio_a_diferentes_estados(self):
        """CA1: La función puede cambiar a diferentes estados, no solo a 'activo'"""
        # Probar cambiar a estado 'cancelado'
        url = reverse('super_admin:modificar_eventos', args=[self.evento_pendiente.id, 'cancelado'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado cambió correctamente
        evento_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        self.assertEqual(evento_actualizado.eve_estado, 'cancelado')
    
    
    def test_informacion_evento_se_mantiene_intacta(self):
        """CA1: Al cambiar el estado, la demás información del evento se mantiene igual"""
        # Capturar información original del evento
        nombre_original = self.evento_pendiente.eve_nombre
        descripcion_original = self.evento_pendiente.eve_descripcion
        capacidad_original = self.evento_pendiente.eve_capacidad
        
        # Cambiar el estado
        url = reverse('super_admin:modificar_eventos', args=[self.evento_pendiente.id, 'activo'])
        self.client.get(url)
        
        # Verificar que la información se mantiene
        evento_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        self.assertEqual(evento_actualizado.eve_nombre, nombre_original)
        self.assertEqual(evento_actualizado.eve_descripcion, descripcion_original)
        self.assertEqual(evento_actualizado.eve_capacidad, capacidad_original)
        self.assertEqual(evento_actualizado.eve_estado, 'activo')  # Solo esto cambió
    
    def test_publicacion_multiples_eventos(self):
        """CA1: Publicación secuencial de múltiples eventos"""
        # Verificar estados iniciales
        self.assertEqual(self.evento_pendiente.eve_estado, 'pendiente')
        self.assertEqual(self.evento_inactivo.eve_estado, 'inactivo')
        
        # Publicar primer evento
        url1 = reverse('super_admin:modificar_eventos', args=[self.evento_pendiente.id, 'activo'])
        response1 = self.client.get(url1)
        self.assertEqual(response1.status_code, 302)
        
        # Publicar segundo evento
        url2 = reverse('super_admin:modificar_eventos', args=[self.evento_inactivo.id, 'activo'])
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 302)
        
        # Verificar que ambos eventos están activos
        evento1_actualizado = Eventos.objects.get(id=self.evento_pendiente.id)
        evento2_actualizado = Eventos.objects.get(id=self.evento_inactivo.id)
        
        self.assertEqual(evento1_actualizado.eve_estado, 'activo')
        self.assertEqual(evento2_actualizado.eve_estado, 'activo')
    
    def test_estados_validos_para_publicacion(self):
        """CA1: Probar diferentes estados válidos para publicación"""
        estados_validos = ['activo', 'publicado', 'live']  # Posibles estados para publicación
        
        for estado in estados_validos:
            with self.subTest(estado=estado):
                # Crear un nuevo evento para cada prueba
                nuevo_evento = Eventos.objects.create(
                    eve_nombre=f'Evento Test {estado}',
                    eve_descripcion='Descripción',
                    eve_ciudad='Bogotá',
                    eve_lugar='Test',
                    eve_fecha_inicio=datetime.now().date() + timedelta(days=5),
                    eve_fecha_fin=datetime.now().date() + timedelta(days=6),
                    eve_estado='pendiente',
                    eve_capacidad=50,
                    eve_tienecosto=False,
                    eve_administrador_fk=self.administrador
                )
                
                url = reverse('super_admin:modificar_eventos', args=[nuevo_evento.id, estado])
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 302)
                
                # Verificar que el estado cambió
                evento_actualizado = Eventos.objects.get(id=nuevo_evento.id)
                self.assertEqual(evento_actualizado.eve_estado, estado)