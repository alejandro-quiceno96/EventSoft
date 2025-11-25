import json
from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from unittest.mock import patch
from app_administrador.models import Administradores
from app_eventos.models import Eventos
from app_certificados.models import Certificado
from app_usuarios.models import Usuario as User

class ModificarCertificadosTestCase(TestCase):
    
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
            eve_nombre="Evento Test Certificado",
            eve_descripcion="Descripción del evento test para certificados",
            eve_ciudad="Ciudad Test",
            eve_lugar="Lugar Test",
            eve_fecha_inicio="2024-01-01",
            eve_fecha_fin="2024-01-02",
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear certificado para el evento
        self.certificado = Certificado.objects.create(
            evento_fk=self.evento,
            firma_nombre="Firmante Test",
            firma_cargo="Director Test",
            orientacion="horizontal",
            certifica="Certifica que completó satisfactoriamente el evento",
            lugar_expedicion="Ciudad Test",
            tipografia="Arial",
            diseño="hola.png",
            firma="firma.png",
        )
        
        self.url = reverse('administrador:modificar_certificados', args=[self.evento.id])
    
    def test_carga_exitosa_pagina(self):
        """CA1: La página carga correctamente con evento y certificado existente"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(self.url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_administrador/modificar_certificado.html')
        
        # Verificar que el contexto contiene los datos esperados
        context = response.context
        self.assertEqual(context['evento'], self.evento)
        self.assertEqual(context['certificado'], self.certificado)
    
    def test_contexto_contiene_fecha_formateada(self):
        """CA2: El contexto contiene una fecha formateada"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(self.url)
        context = response.context
        
        # Verificar que existe fecha_actual en el contexto
        self.assertIn('fecha_actual', context)
        fecha_actual = context['fecha_actual']
        
        # Verificar que es un string (sin especificar formato exacto)
        self.assertIsInstance(fecha_actual, str)
        # No verificamos el contenido específico porque depende del locale del sistema
    
    def test_contexto_contiene_orientacion(self):
        """CA2: El contexto contiene la orientación del certificado"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(self.url)
        context = response.context
        
        # Verificar que existe orientacion en el contexto
        self.assertIn('orientacion', context)
        self.assertEqual(context['orientacion'], self.certificado.orientacion)
    
    def test_evento_no_existente(self):
        """CA3: Evento que no existe retorna error 404"""
        self.client.login(username='admin_test', password='testpass123')
        
        url_invalida = reverse('administrador:modificar_certificados', args=[999])  # ID que no existe
        
        response = self.client.get(url_invalida)
        
        self.assertEqual(response.status_code, 404)
    
    def test_certificado_no_existente(self):
        """CA3: Certificado que no existe retorna error 404"""
        # Crear un evento sin certificado
        evento_sin_certificado = Eventos.objects.create(
            eve_nombre="Evento Sin Certificado",
            eve_descripcion="Evento sin certificado asociado",
            eve_ciudad="Ciudad Test",
            eve_lugar="Lugar Test",
            eve_fecha_inicio="2024-01-01",
            eve_fecha_fin="2024-01-02",
            eve_estado="Activo",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        self.client.login(username='admin_test', password='testpass123')
        url_sin_certificado = reverse('administrador:modificar_certificados', args=[evento_sin_certificado.id])
        
        response = self.client.get(url_sin_certificado)
        
        self.assertEqual(response.status_code, 404)
    
    def test_acceso_sin_autenticar(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        response = self.client.get(self.url)
        
        # Verificar redirección a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_datos_certificado_en_contexto(self):
        """CA1: Todos los datos del certificado están disponibles en el contexto"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(self.url)
        context = response.context
        
        # Verificar datos específicos del certificado a través del contexto
        certificado_context = context['certificado']
        self.assertEqual(certificado_context.firma_nombre, "Firmante Test")
        self.assertEqual(certificado_context.firma_cargo, "Director Test")
        self.assertEqual(certificado_context.certifica, "Certifica que completó satisfactoriamente el evento")
        self.assertEqual(certificado_context.lugar_expedicion, "Ciudad Test")
        self.assertEqual(certificado_context.tipografia, "Arial")
