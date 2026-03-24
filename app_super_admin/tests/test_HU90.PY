import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from collections import defaultdict
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from app_areas.models import Areas

User = get_user_model()

class SuperAdminIndexTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # Crear administradores de eventos
        self.admin1 = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='testpass123'
        )
        
        self.admin2 = User.objects.create_user(
            username='admin2', 
            email='admin2@example.com',
            password='testpass123'
        )
        
        self.administrador1 = Administradores.objects.create(
            usuario=self.admin1,
            estado='Activo'
        )
        
        self.administrador2 = Administradores.objects.create(
            usuario=self.admin2,
            estado='Activo'
        )
        
        # Crear áreas
        self.area1 = Areas.objects.create(are_nombre='Tecnología')
        self.area2 = Areas.objects.create(are_nombre='Ciencias')
        
        # Crear eventos con diferentes estados
        hoy = datetime.now().date()
        
        # Eventos activos
        self.evento_activo1 = Eventos.objects.create(
            eve_nombre='Conferencia Tech 2024',
            eve_descripcion='Conferencia de tecnología',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen='evento1.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador1
        )
        
        self.evento_activo2 = Eventos.objects.create(
            eve_nombre='Workshop Ciencia',
            eve_descripcion='Taller de ciencias',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='activo',
            eve_imagen='evento2.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador2
        )
        
        # Eventos pendientes
        self.evento_pendiente1 = Eventos.objects.create(
            eve_nombre='Evento Pendiente 1',
            eve_descripcion='Evento en revisión',
            eve_ciudad='Cali',
            eve_lugar='Lugar X',
            eve_fecha_inicio=hoy + timedelta(days=20),
            eve_fecha_fin=hoy + timedelta(days=21),
            eve_estado='pendiente',
            eve_imagen='evento3.jpg',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador1
        )
        
        self.evento_pendiente2 = Eventos.objects.create(
            eve_nombre='Evento Pendiente 2',
            eve_descripcion='Otro evento en revisión',
            eve_ciudad='Barranquilla',
            eve_lugar='Lugar Y',
            eve_fecha_inicio=hoy + timedelta(days=25),
            eve_fecha_fin=hoy + timedelta(days=26),
            eve_estado='pendiente',
            eve_imagen='evento4.jpg',
            eve_capacidad=30,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador2
        )
        
        # Evento inactivo
        self.evento_inactivo = Eventos.objects.create(
            eve_nombre='Evento Inactivo',
            eve_descripcion='Evento finalizado',
            eve_ciudad='Cartagena',
            eve_lugar='Lugar Z',
            eve_fecha_inicio=hoy - timedelta(days=10),
            eve_fecha_fin=hoy - timedelta(days=8),
            eve_estado='inactivo',
            eve_imagen='evento5.jpg',
            eve_capacidad=80,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador1
        )
        
        # URL para los tests
        self.url = reverse('super_admin:index_super_admin')  # Ajusta según tu URL name
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def test_acceso_pagina_index(self):
        """CA1: La página de inicio del super admin carga correctamente"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_super_admin/inicio_super_admin.html')
    
    def test_muestra_todos_los_eventos(self):
        """CA1: Muestra todos los eventos sin filtrar"""
        response = self.client.get(self.url)
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar todos los eventos (5 en total)
        self.assertEqual(eventos.count(), 5)
        
        # Verificar que están todos los eventos
        eventos_nombres = [evento.eve_nombre for evento in eventos]
        self.assertIn('Conferencia Tech 2024', eventos_nombres)
        self.assertIn('Workshop Ciencia', eventos_nombres)
        self.assertIn('Evento Pendiente 1', eventos_nombres)
        self.assertIn('Evento Pendiente 2', eventos_nombres)
        self.assertIn('Evento Inactivo', eventos_nombres)
    
    def test_eventos_con_administradores(self):
        """CA1: Los eventos incluyen información de sus administradores"""
        response = self.client.get(self.url)
        
        context = response.context
        eventos = context['eventos']
        
        # Verificar que los eventos tienen la relación con administradores
        for evento in eventos:
            self.assertIsNotNone(evento.eve_administrador_fk)
            self.assertIsNotNone(evento.eve_administrador_fk.usuario)
            self.assertIsNotNone(evento.eve_administrador_fk.usuario.username)
    
    def test_agrupacion_por_estado(self):
        """CA2: Agrupa eventos correctamente por estado"""
        response = self.client.get(self.url)
        
        context = response.context
        eventos_por_estado = context['eventos_por_estado']
        
        # Verificar que se agrupan por estado (capitalizado)
        self.assertIn('Activo', eventos_por_estado)
        self.assertIn('Pendiente', eventos_por_estado)
        self.assertIn('Inactivo', eventos_por_estado)
        
        # Verificar cantidad de eventos por estado
        self.assertEqual(len(eventos_por_estado['Activo']), 2)
        self.assertEqual(len(eventos_por_estado['Pendiente']), 2)
        self.assertEqual(len(eventos_por_estado['Inactivo']), 1)
    
    def test_contador_eventos_pendientes(self):
        """CA2: Cuenta correctamente los eventos pendientes"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Verificar contador de eventos pendientes
        self.assertEqual(context['pendientes_count'], 2)
    
    def test_contexto_completo(self):
        """CA3: Proporciona todos los datos de contexto necesarios"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Verificar que el contexto tiene todos los elementos esperados
        self.assertIn('eventos', context)
        self.assertIn('eventos_por_estado', context)
        self.assertIn('pendientes_count', context)
        self.assertIn('areas', context)
        
        # Verificar tipos de datos
        self.assertIsInstance(context['eventos_por_estado'], defaultdict)
        self.assertIsInstance(context['pendientes_count'], int)
        self.assertIsInstance(context['areas'].first(), Areas)
    
    def test_areas_en_contexto(self):
        """CA3: Las áreas están disponibles en el contexto"""
        response = self.client.get(self.url)
        
        context = response.context
        areas = context['areas']
        
        # Verificar que se incluyen todas las áreas
        self.assertEqual(areas.count(), 2)
        areas_nombres = [area.are_nombre for area in areas]
        self.assertIn('Tecnología', areas_nombres)
        self.assertIn('Ciencias', areas_nombres)
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado es redirigido"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
