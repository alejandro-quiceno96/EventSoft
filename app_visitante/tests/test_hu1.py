import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_eventos.models import Eventos
from app_categorias.models import Categorias
from app_areas.models import Areas
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores

User = get_user_model()

class InicioVisitanteTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        self.url = reverse('inicio_visitante')  # Ajusta según tu URL name
        
        # Crear áreas y categorías de prueba
        self.area1 = Areas.objects.create(are_nombre='Tecnología')
        self.area2 = Areas.objects.create(are_nombre='Ciencias')
        
        self.categoria1 = Categorias.objects.create(
            cat_nombre='Programación',
            cat_area_fk=self.area1
        )
        self.categoria2 = Categorias.objects.create(
            cat_nombre='Inteligencia Artificial',
            cat_area_fk=self.area1
        )
        self.categoria3 = Categorias.objects.create(
            cat_nombre='Biología',
            cat_area_fk=self.area2
        )
        
        # Crear usuarios de prueba
        self.user_normal = User.objects.create_user(
            username='usernormal',
            email='normal@example.com',
            password='testpass123'
        )
        
        self.user_admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.user_super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='testpass123'
        )
        
        # Crear administradores
        self.administrador = Administradores.objects.create(
            usuario=self.user_admin,
            estado='Activo'
        )
        
        self.super_administrador = SuperAdministradores.objects.create(
            usuario=self.user_super_admin
        )
        
        # Crear eventos de prueba
        hoy = datetime.date.today()
        
        # Eventos activos futuros
        self.evento1 = Eventos.objects.create(
            eve_nombre='Conferencia Python',
            eve_descripcion='Conferencia sobre Python',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + datetime.timedelta(days=10),
            eve_fecha_fin=hoy + datetime.timedelta(days=12),
            eve_estado='activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen='imagen.png'  # Agrega otros campos necesarios
        )
        self.evento1.eventoscategorias_set.create(eve_cat_categoria_fk=self.categoria1)
        
        self.evento2 = Eventos.objects.create(
            eve_nombre='Workshop AI',
            eve_descripcion='Taller de Inteligencia Artificial',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + datetime.timedelta(days=15),
            eve_fecha_fin=hoy + datetime.timedelta(days=16),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador,
            eve_imagen='imagen.png'
        )
        self.evento2.eventoscategorias_set.create(eve_cat_categoria_fk=self.categoria2)
        
        # Evento inactivo (no debería aparecer)
        self.evento_inactivo = Eventos.objects.create(
            eve_nombre='Evento Inactivo',
            eve_descripcion='Este evento no está activo',
            eve_ciudad='Cali',
            eve_lugar='Lugar X',
            eve_fecha_inicio=hoy + datetime.timedelta(days=20),
            eve_fecha_fin=hoy + datetime.timedelta(days=21),
            eve_estado='inactivo',  # Estado diferente a "activo"
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen='imagen.png'
        )
        
        # Evento pasado (no debería aparecer)
        self.evento_pasado = Eventos.objects.create(
            eve_nombre='Evento Pasado',
            eve_descripcion='Este evento ya pasó',
            eve_ciudad='Barranquilla',
            eve_lugar='Lugar Y',
            eve_fecha_inicio=hoy - datetime.timedelta(days=10),
            eve_fecha_fin=hoy - datetime.timedelta(days=8),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,
            eve_imagen='imagen.png'
        )
    
    def test_acceso_pagina_inicio(self):
        """CA1: La página de inicio carga correctamente"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/index.html')
    
    def test_muestra_eventos_activos_futuros(self):
        """CA1: Muestra solo eventos activos con fecha futura"""
        response = self.client.get(self.url)
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar solo eventos activos futuros
        self.assertEqual(eventos.count(), 2)
        
        # Verificar que están los eventos correctos
        eventos_nombres = [evento.eve_nombre for evento in eventos]
        self.assertIn('Conferencia Python', eventos_nombres)
        self.assertIn('Workshop AI', eventos_nombres)
        self.assertNotIn('Evento Inactivo', eventos_nombres)
        self.assertNotIn('Evento Pasado', eventos_nombres)
    
    def test_filtro_por_categoria(self):
        """CA1: Filtra eventos por categoría"""
        response = self.client.get(self.url, {'categoria': self.categoria1.id})
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar solo eventos de la categoría Programación
        self.assertEqual(eventos.count(), 1)
        self.assertEqual(eventos[0].eve_nombre, 'Conferencia Python')
    
    def test_filtro_por_area(self):
        """CA1: Filtra eventos por área"""
        response = self.client.get(self.url, {'area': self.area1.id})
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar eventos de Tecnología (Programación y AI)
        self.assertEqual(eventos.count(), 2)
    
    def test_filtro_por_fecha_inicio(self):
        """CA1: Filtra eventos por fecha de inicio específica"""
        fecha_especifica = self.evento1.eve_fecha_inicio
        
        response = self.client.get(self.url, {'fecha_inicio': fecha_especifica})
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar solo el evento que empieza en esa fecha
        self.assertEqual(eventos.count(), 1)
        self.assertEqual(eventos[0].eve_nombre, 'Conferencia Python')
    
    def test_filtros_combinados(self):
        """CA1: Filtros combinados funcionan correctamente"""
        response = self.client.get(self.url, {
            'area': self.area1.id,
            'categoria': self.categoria2.id
        })
        
        context = response.context
        eventos = context['eventos']
        
        # Debería mostrar solo eventos de IA en Tecnología
        self.assertEqual(eventos.count(), 1)
        self.assertEqual(eventos[0].eve_nombre, 'Workshop AI')
    
    def test_contexto_contiene_categorias_y_areas(self):
        """CA3: El contexto contiene categorías y áreas"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Verificar que el contexto tiene todos los elementos esperados
        self.assertIn('categorias', context)
        self.assertIn('areas', context)
        self.assertIn('roles', context)
        self.assertIn('estado_admin', context)
        
        # Verificar datos específicos
        self.assertEqual(context['categorias'].count(), 3)
        self.assertEqual(context['areas'].count(), 2)
    
    def test_usuario_no_autenticado(self):
        """CA2: Usuario no autenticado no tiene roles"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Usuario no autenticado no debería tener roles
        self.assertEqual(context['roles'], [])
        self.assertIsNone(context['estado_admin'])
    
    def test_usuario_normal_autenticado(self):
        """CA2: Usuario normal autenticado sin roles especiales"""
        self.client.login(username='usernormal', password='testpass123')
        
        response = self.client.get(self.url)
        
        context = response.context
        
        # Usuario normal no debería tener roles especiales
        self.assertEqual(context['roles'], [])
        self.assertIsNone(context['estado_admin'])
    
    def test_usuario_administrador_activo(self):
        """CA2: Usuario con rol de Administrador activo"""
        self.client.login(username='adminuser', password='testpass123')
        
        response = self.client.get(self.url)
        
        context = response.context
        
        # Debería tener rol de Administrador de Eventos
        self.assertIn('Administrador de Eventos', context['roles'])
        self.assertEqual(context['estado_admin'], 'Activo')
    
    def test_usuario_super_administrador(self):
        """CA2: Usuario con rol de Super Administrador"""
        self.client.login(username='superadmin', password='testpass123')
        
        response = self.client.get(self.url)
        
        context = response.context
        
        # Debería tener rol de Super Administrador
        self.assertIn('Super Administrador', context['roles'])
        # Super admin no tiene estado_admin
        self.assertIsNone(context['estado_admin'])
    
    def test_usuario_con_multiples_roles(self):
        """CA2: Usuario con múltiples roles"""
        # Crear usuario con ambos roles
        user_multi = User.objects.create_user(
            username='multiuser',
            email='multi@example.com',
            password='testpass123'
        )
        
        Administradores.objects.create(usuario=user_multi, estado='Activo')
        SuperAdministradores.objects.create(usuario=user_multi)
        
        self.client.login(username='multiuser', password='testpass123')
        
        response = self.client.get(self.url)
        
        context = response.context
        
        # Debería tener ambos roles
        self.assertIn('Super Administrador', context['roles'])
        self.assertIn('Administrador de Eventos', context['roles'])
        self.assertEqual(len(context['roles']), 2)
        self.assertEqual(context['estado_admin'], 'Activo')

