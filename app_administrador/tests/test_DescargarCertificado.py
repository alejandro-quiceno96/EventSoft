import json
import locale
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from app_eventos.models import Eventos
from app_certificados.models import Certificado
from app_administrador.models import Administradores

User = get_user_model()

class DescargarCertificadoPdfTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.user_admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.administrador = Administradores.objects.create(
            usuario=self.user_admin,
            estado='Activo'
        )
        
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Conferencia de Prueba',
            eve_descripcion='Descripción del evento prueba',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=datetime.now().date() + timedelta(days=10),
            eve_fecha_fin=datetime.now().date() + timedelta(days=12),
            eve_estado='activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear certificado para el evento
        self.certificado = Certificado.objects.create(
            evento_fk=self.evento,
            firma_nombre='Dr. Juan Pérez',
            firma_cargo='Director del Evento',
            orientacion='horizontal',
            certifica='Certifica que el participante completó satisfactoriamente el evento',
            lugar_expedicion='Bogotá, D.C.',
            tipografia='Arial'
        )
        
        # URL para los tests - AJUSTA SEGÚN TU URL NAME
        self.url = reverse('administrador:descargar_certificado_pdf', args=[self.evento.id])  # Sin namespace
        
        # Autenticar como administrador
        self.client.login(username='admin', password='testpass123')
    
    @patch('app_administrador.views.HTML')
    @patch('app_administrador.views.render_to_string')
    def test_genera_pdf_exitoso(self, mock_render_to_string, mock_html_class):
        """CA1: Genera PDF exitosamente con datos correctos"""
        # Mock de render_to_string
        mock_render_to_string.return_value = '<html>Certificado mock</html>'
        
        # Mock de WeasyPrint HTML
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'%PDF-1.4 mock pdf content'
        mock_html_class.return_value = mock_html_instance
        
        response = self.client.get(self.url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
        # Verificar headers de descarga
        self.assertIn('inline', response['Content-Disposition'])
        self.assertIn(f'certificado_{self.evento.id}.pdf', response['Content-Disposition'])
        
        # Verificar contenido PDF
        self.assertEqual(response.content, b'%PDF-1.4 mock pdf content')
        
        # Verificar que se llamó a render_to_string con los parámetros correctos
        mock_render_to_string.assert_called_once()
        call_args = mock_render_to_string.call_args
        
        # render_to_string usa argumentos posicionales: (template_name, context)
        self.assertEqual(call_args[0][0], 'app_administrador/pdf_certificado.html')
        
        # El contexto es el segundo argumento posicional
        context = call_args[0][1] if len(call_args[0]) > 1 else {}
        self.assertEqual(context['certificado'], self.certificado)
        self.assertEqual(context['evento'], self.evento)
        self.assertIn('now', context)
    
    @patch('app_administrador.views.HTML')
    @patch('app_administrador.views.render_to_string')
    def test_contexto_plantilla_correcto(self, mock_render_to_string, mock_html_class):
        """CA1: El contexto pasado a la plantilla es correcto"""
        # Configurar mocks
        mock_render_to_string.return_value = '<html>Certificado</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'pdf content'
        mock_html_class.return_value = mock_html_instance
        
        response = self.client.get(self.url)
        
        # Verificar que se pasaron los datos correctos al contexto
        mock_render_to_string.assert_called_once()
        call_args = mock_render_to_string.call_args
        
        # El contexto es el segundo argumento posicional
        context = call_args[0][1] if len(call_args[0]) > 1 else {}
        
        # Verificar datos del certificado
        self.assertEqual(context['certificado'].firma_nombre, 'Dr. Juan Pérez')
        self.assertEqual(context['certificado'].firma_cargo, 'Director del Evento')
        self.assertEqual(context['certificado'].orientacion, 'horizontal')
        self.assertEqual(context['certificado'].certifica, 'Certifica que el participante completó satisfactoriamente el evento')
        self.assertEqual(context['certificado'].lugar_expedicion, 'Bogotá, D.C.')
        self.assertEqual(context['certificado'].tipografia, 'Arial')
        
        # Verificar datos del evento
        self.assertEqual(context['evento'].eve_nombre, 'Conferencia de Prueba')
        self.assertEqual(context['evento'].eve_ciudad, 'Bogotá')
        
        # Verificar que la fecha está formateada
        self.assertIsInstance(context['now'], str)
        self.assertIn('de', context['now'])  # Formato en español
    
    @patch('app_administrador.views.locale.setlocale')
    @patch('app_administrador.views.HTML')
    @patch('app_administrador.views.render_to_string')
    def test_configuracion_locale_espanol(self, mock_render_to_string, mock_html_class, mock_setlocale):
        """CA2: Configura correctamente el locale para español"""
        # Configurar mocks
        mock_render_to_string.return_value = '<html>Certificado</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'pdf content'
        mock_html_class.return_value = mock_html_instance
        
        response = self.client.get(self.url)
        
        # Verificar que se intentó configurar el locale (al menos una vez)
        mock_setlocale.assert_called()
        
        # Verificar que al menos se intentó con algún locale español
        locale_calls = [call[0] for call in mock_setlocale.call_args_list]
        spanish_locales = [call for call in locale_calls if 'es' in str(call[1])]
        self.assertGreater(len(spanish_locales), 0)
    
    @patch('app_administrador.views.locale.setlocale')
    @patch('app_administrador.views.HTML')
    @patch('app_administrador.views.render_to_string')
    def test_locale_fallback(self, mock_render_to_string, mock_html_class, mock_setlocale):
        """CA2: Maneja fallbacks de locale correctamente"""
        # Configurar mock para que falle con el primer locale
        mock_setlocale.side_effect = [
            locale.Error,  # Falla con el primer intento
            None           # Funciona con el segundo intento
        ]
        
        mock_render_to_string.return_value = '<html>Certificado</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'pdf content'
        mock_html_class.return_value = mock_html_instance
        
        response = self.client.get(self.url)
        
        # Verificar que se intentó al menos dos veces
        self.assertGreaterEqual(mock_setlocale.call_count, 2)
    
    def test_evento_no_existente(self):
        """CA3: Evento que no existe retorna 404"""
        url_invalida = reverse('administrador:descargar_certificado_pdf', args=[9999])
        
        response = self.client.get(url_invalida)
        
        self.assertEqual(response.status_code, 404)
    
    def test_certificado_no_existente(self):
        """CA3: Certificado que no existe retorna 404"""
        # Crear evento sin certificado
        evento_sin_certificado = Eventos.objects.create(
            eve_nombre='Evento Sin Certificado',
            eve_descripcion='Evento sin certificado',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=datetime.now().date() + timedelta(days=5),
            eve_fecha_fin=datetime.now().date() + timedelta(days=6),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        url_sin_certificado = reverse('administrador:descargar_certificado_pdf', args=[evento_sin_certificado.id])
        
        response = self.client.get(url_sin_certificado)
        
        self.assertEqual(response.status_code, 404)
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado es redirigido"""
        client_no_auth = Client()
        response = client_no_auth.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
