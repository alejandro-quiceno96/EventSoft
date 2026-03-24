import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes

User = get_user_model()

class InicioAsistenteTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario asistente
        self.usuario_asistente = User.objects.create_user(
            username='asistente',
            email='asistente@example.com',
            password='testpass123'
        )
        
        # Crear perfil de asistente
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)
        
        # Crear asistente sin eventos
        self.usuario_sin_eventos = User.objects.create_user(
            username='asistente_sin_eventos',
            email='sin_eventos@example.com',
            password='testpass123'
        )
        self.asistente_sin_eventos = Asistentes.objects.create(usuario=self.usuario_sin_eventos)
        
        # Crear administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.administrador = Administradores.objects.create(usuario=self.admin_user)
        
        # Crear eventos
        hoy = timezone.now().date()
        
        self.evento1 = Eventos.objects.create(
            eve_nombre='Conferencia de Tecnología',
            eve_descripcion='Conferencia sobre nuevas tecnologías',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen=SimpleUploadedFile("evento1.jpg", b"file_content1", content_type="image/jpeg"),
            eve_capacidad=100,
            eve_tienecosto=True,
            eve_memorias='https://example.com/memorias1',
            eve_administrador_fk=self.administrador
        )
        
        self.evento2 = Eventos.objects.create(
            eve_nombre='Workshop de Programación',
            eve_descripcion='Taller práctico de programación',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='activo',
            eve_imagen=SimpleUploadedFile("evento2.jpg", b"file_content2", content_type="image/jpeg"),
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_memorias='https://example.com/memorias2',
            eve_administrador_fk=self.administrador
        )
        
        # Crear inscripciones para el asistente
        self.inscripcion1 = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento1,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte1.pdf", b"file_content1", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr1.pdf", b"qr_content1", content_type="application/pdf"),
            asi_eve_clave='CLAVE123'
        )
        
        self.inscripcion2 = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento2,
            asi_eve_estado='Pendiente',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE456'
        )
        
        # URL para los tests
        self.url = reverse('app_asistente:inicio_asistente')
        
        # Autenticar como asistente con eventos
        self.client.login(username='asistente', password='testpass123')

    def test_acceso_pagina_inicio_asistente(self):
        """CA3: La página de inicio del asistente carga correctamente"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_asistente/eventos_asistentes.html')

    def test_listado_eventos_inscritos(self):
        """CA1: Listado correcto de todos los eventos donde el asistente está inscrito"""
        response = self.client.get(self.url)
        
        context = response.context
        eventos = context['eventos']
        cedula_participante = context['cedula_participante']
        
        # Verificar que se retorna el ID del asistente
        self.assertEqual(cedula_participante, self.asistente.id)
        
        # Verificar que se retornan todos los eventos inscritos (2 eventos)
        self.assertEqual(len(eventos), 2)
        
        # Verificar estructura de cada evento
        for evento in eventos:
            self.assertIn('eve_id', evento)
            self.assertIn('eve_nombre', evento)
            self.assertIn('eve_fecha_inicio', evento)
            self.assertIn('eve_fecha_fin', evento)
            self.assertIn('eve_imagen', evento)
            self.assertIn('asi_eve_estado', evento)
            self.assertIn('eve_memorias', evento)
        
        # Verificar que están todos los eventos
        eventos_nombres = [evento['eve_nombre'] for evento in eventos]
        self.assertIn('Conferencia de Tecnología', eventos_nombres)
        self.assertIn('Workshop de Programación', eventos_nombres)

    def test_datos_correctos_eventos(self):
        """CA1: Verificar que los datos de los eventos son correctos"""
        response = self.client.get(self.url)
        eventos = response.context['eventos']
        
        # Encontrar cada evento por nombre
        evento_conf = next(e for e in eventos if e['eve_nombre'] == 'Conferencia de Tecnología')
        evento_workshop = next(e for e in eventos if e['eve_nombre'] == 'Workshop de Programación')
        
        # Verificar datos del primer evento
        self.assertEqual(evento_conf['eve_id'], self.evento1.id)
        self.assertEqual(evento_conf['asi_eve_estado'], 'Admitido')
        self.assertEqual(evento_conf['eve_memorias'], 'https://example.com/memorias1')
        self.assertEqual(str(evento_conf['eve_fecha_inicio']), str(self.evento1.eve_fecha_inicio))
        
        # Verificar datos del segundo evento
        self.assertEqual(evento_workshop['eve_id'], self.evento2.id)
        self.assertEqual(evento_workshop['asi_eve_estado'], 'Pendiente')
        self.assertEqual(evento_workshop['eve_memorias'], 'https://example.com/memorias2')

    def test_asistente_sin_eventos(self):
        """CA2: Asistente sin eventos inscritos"""
        # Autenticar como asistente sin eventos
        self.client.login(username='asistente_sin_eventos', password='testpass123')
        
        response = self.client.get(self.url)
        
        context = response.context
        eventos = context['eventos']
        cedula_participante = context['cedula_participante']
        
        # Verificar que se retorna el ID del asistente
        self.assertEqual(cedula_participante, self.asistente_sin_eventos.id)
        
        # Verificar que no hay eventos
        self.assertEqual(len(eventos), 0)
        self.assertEqual(eventos, [])

    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado - COMPORTAMIENTO: función maneja excepción"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        # La función maneja la excepción y retorna el template con lista vacía
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_asistente/eventos_asistentes.html')
        
        context = response.context
        self.assertEqual(context['eventos'], [])
        self.assertIsNone(context['cedula_participante'])

    def test_estados_diferentes_inscripciones(self):
        """CA1: Verificar que se incluyen eventos con diferentes estados de inscripción"""
        response = self.client.get(self.url)
        eventos = response.context['eventos']
        
        # Verificar que se incluyen eventos con diferentes estados
        estados = [evento['asi_eve_estado'] for evento in eventos]
        self.assertIn('Admitido', estados)
        self.assertIn('Pendiente', estados)

    def test_contexto_completo(self):
        """CA3: Contexto contiene todos los datos necesarios"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Verificar que el contexto tiene los elementos esperados
        self.assertIn('eventos', context)
        self.assertIn('cedula_participante', context)
        
        # Verificar tipos de datos
        self.assertIsInstance(context['eventos'], list)
        self.assertIsInstance(context['cedula_participante'], int)

    def test_usuario_sin_perfil_asistente(self):
        """CA2: Usuario autenticado pero sin perfil de asistente"""
        # Crear usuario normal sin perfil de asistente
        usuario_normal = User.objects.create_user(
            username='usuario_normal',
            email='normal@example.com',
            password='testpass123'
        )
        
        self.client.login(username='usuario_normal', password='testpass123')
        response = self.client.get(self.url)
        
        # La función debería manejar el DoesNotExist y retornar template vacío
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_asistente/eventos_asistentes.html')
        
        context = response.context
        self.assertEqual(context['eventos'], [])
        self.assertIsNone(context['cedula_participante'])