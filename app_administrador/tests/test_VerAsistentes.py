import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores

User = get_user_model()

class VerAsistentesTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuarios
        self.user_admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            telefono='3001234567'
        )
        
        self.user_asistente1 = User.objects.create_user(
            username='asistente1',
            email='asistente1@example.com',
            password='testpass123',
            first_name='Juan',
            last_name='Perez',
            telefono='3001111111'
        )
        
        self.user_asistente2 = User.objects.create_user(
            username='asistente2',
            email='asistente2@example.com',
            password='testpass123',
            first_name='Maria',
            last_name='Gomez',
            telefono='3002222222'
        )
        
        self.user_asistente3 = User.objects.create_user(
            username='asistente3',
            email='asistente3@example.com',
            password='testpass123',
            first_name='Carlos',
            last_name='Lopez',
            telefono='3003333333'
        )
        
        # Crear administrador
        self.administrador = Administradores.objects.create(
            usuario=self.user_admin,
            estado='Activo'
        )
        
        # Crear asistentes
        self.asistente1 = Asistentes.objects.create(usuario=self.user_asistente1)
        self.asistente2 = Asistentes.objects.create(usuario=self.user_asistente2)
        self.asistente3 = Asistentes.objects.create(usuario=self.user_asistente3)
        
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Conferencia de Prueba',
            eve_descripcion='Descripción del evento',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=datetime.now().date() + timedelta(days=10),
            eve_fecha_fin=datetime.now().date() + timedelta(days=12),
            eve_estado='activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear archivo simulado para soporte
        self.archivo_soporte = SimpleUploadedFile(
            "soporte.pdf", 
            b"file_content", 
            content_type="application/pdf"
        )
        
        # Crear relaciones AsistentesEventos con diferentes estados
        self.asistente_evento1 = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente1,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=self.archivo_soporte,
            asi_eve_fecha_hora=now()
        )
        
        self.asistente_evento2 = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente2,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Pendiente',
            asi_eve_soporte=None,
            asi_eve_fecha_hora=now() - timedelta(hours=1)
        )
        
        self.asistente_evento3 = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente3,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Rechazado',
            asi_eve_soporte=self.archivo_soporte,
            asi_eve_fecha_hora=now() - timedelta(hours=2)
        )
        
        # URL para los tests
        self.url = reverse('administrador:ver_asistentes', args=[self.evento.id])
        
        # Autenticar como administrador
        self.client.login(username='admin', password='testpass123')
    
    def test_acceso_pagina_ver_asistentes(self):
        """CA1: La página de asistentes carga correctamente"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_administrador/ver_asistentes.html')
    
    def test_muestra_asistentes_sin_filtro_estado(self):
        """CA1: Muestra todos los asistentes sin filtro de estado"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Debería tener datos básicos en el contexto
        self.assertIn('asistentes', context)
        self.assertIn('evento', context)
        self.assertIn('evento_nombre', context)
        self.assertIn('asistentes_admitidos', context)
        
        # El evento debería ser el correcto
        self.assertEqual(context['evento'].id, self.evento.id)
        self.assertEqual(context['evento_nombre'], 'Conferencia de Prueba')
    
    def test_filtro_estado_admitido(self):
        """CA1: Filtra asistentes por estado 'Admitido'"""
        response = self.client.get(self.url, {'estado': 'Admitido'})
        
        context = response.context
        asistentes = context['asistentes']
        
        # Debería mostrar solo 1 asistente admitido
        self.assertEqual(len(asistentes), 1)
        self.assertEqual(asistentes[0]['asi_nombre'], 'Juan Perez')
        self.assertEqual(asistentes[0]['estado'], 'Admitido')
        self.assertIsNotNone(asistentes[0]['documentos'])  # Tiene soporte
    
    def test_filtro_estado_pendiente(self):
        """CA1: Filtra asistentes por estado 'Pendiente'"""
        response = self.client.get(self.url, {'estado': 'Pendiente'})
        
        context = response.context
        asistentes = context['asistentes']
        
        # Debería mostrar solo 1 asistente pendiente
        self.assertEqual(len(asistentes), 1)
        self.assertEqual(asistentes[0]['asi_nombre'], 'Maria Gomez')
        self.assertEqual(asistentes[0]['estado'], 'Pendiente')
        self.assertIsNone(asistentes[0]['documentos'])  # No tiene soporte
    
    def test_filtro_estado_rechazado(self):
        """CA1: Filtra asistentes por estado 'Rechazado'"""
        response = self.client.get(self.url, {'estado': 'Rechazado'})
        
        context = response.context
        asistentes = context['asistentes']
        
        # Debería mostrar solo 1 asistente rechazado
        self.assertEqual(len(asistentes), 1)
        self.assertEqual(asistentes[0]['asi_nombre'], 'Carlos Lopez')
        self.assertEqual(asistentes[0]['estado'], 'Rechazado')
        self.assertIsNotNone(asistentes[0]['documentos'])  # Tiene soporte
    
    def test_estructura_datos_asistentes(self):
        """CA2: Los datos de asistentes tienen estructura correcta"""
        response = self.client.get(self.url, {'estado': 'Admitido'})
        
        context = response.context
        asistentes = context['asistentes']
        
        # Verificar estructura completa del primer asistente
        asistente = asistentes[0]
        
        self.assertIn('asi_id', asistente)
        self.assertIn('asi_nombre', asistente)
        self.assertIn('asi_correo', asistente)
        self.assertIn('asi_telefono', asistente)
        self.assertIn('documentos', asistente)
        self.assertIn('estado', asistente)
        self.assertIn('hora_inscripcion', asistente)
        
        # Verificar valores específicos
        self.assertEqual(asistente['asi_nombre'], 'Juan Perez')
        self.assertEqual(asistente['asi_correo'], 'asistente1@example.com')
        self.assertEqual(asistente['asi_telefono'], '3001111111')
        self.assertEqual(asistente['estado'], 'Admitido')
        self.assertIsNotNone(asistente['hora_inscripcion'])
    
    def test_contador_asistentes_admitidos(self):
        """CA2: Contador de asistentes admitidos es correcto"""
        response = self.client.get(self.url)
        
        context = response.context
        
        # Debería contar correctamente los asistentes admitidos
        self.assertEqual(context['asistentes_admitidos'], 1)
    
    def test_fechas_en_contexto(self):
        """CA2: Fechas del evento y actual en contexto"""
        response = self.client.get(self.url)
        
        context = response.context
        
        self.assertIn('evento_fecha_fin', context)
        self.assertIn('fecha_actual', context)
        
        # Verificar formato ISO
        self.assertEqual(context['evento_fecha_fin'], self.evento.eve_fecha_fin.isoformat())
        self.assertIsInstance(context['fecha_actual'], str)
    
    def test_evento_no_existente(self):
        """CA3: Evento que no existe retorna 404"""
        url_invalida = reverse('administrador:ver_asistentes', args=[9999])  # ID que no existe
        
        response = self.client.get(url_invalida)
        
        self.assertEqual(response.status_code, 404)
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado es redirigido"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_sin_asistentes_en_estado(self):
        """CA1: Sin asistentes en estado específico"""
        # Estado que no tiene asistentes
        response = self.client.get(self.url, {'estado': 'NoExiste'})
        
        context = response.context
        asistentes = context['asistentes']
        
        # Debería retornar lista vacía
        self.assertEqual(len(asistentes), 0)

