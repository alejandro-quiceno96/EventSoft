from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from app_eventos.models import Eventos, EvaluadoresEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from unittest.mock import patch
from django.conf import settings
from app_certificados.models import Certificado

from app_evaluador.models import Evaluadores


class EnviarCertificadoEvaluadoresTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='12345678',
            first_name='Admin',
            last_name='Test'
        )
        
        # Crear perfil de administrador
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo'
        )
        
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test Evaluadores',
            eve_descripcion='Descripción del evento test para evaluadores',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear certificado para el evento
        self.certificado = Certificado.objects.create(
            evento_fk=self.evento,
            firma_nombre='Director General',
            firma_cargo='Director',
            certifica='Por haber participado como evaluador en el evento',
            lugar_expedicion='Bogotá, D.C.',
            tipografia='Arial',
            diseño=SimpleUploadedFile("diseño.png", b"file_content"),
            firma=SimpleUploadedFile("firma.png", b"file_content")
        )
        
        # Crear evaluadores y sus relaciones con el evento
        self.evaluadores_data = [
            {
                'username': 'evaluador1',
                'email': 'evaluador1@test.com',
                'documento': '11111111',
                'estado': 'Admitido',
                'first_name': 'Carlos',
                'last_name': 'Hernández'
            },
            {
                'username': 'evaluador2', 
                'email': 'evaluador2@test.com',
                'documento': '22222222',
                'estado': 'Admitido',
                'first_name': 'Laura',
                'last_name': 'Ramírez'
            },
            {
                'username': 'evaluador3',
                'email': 'evaluador3@test.com', 
                'documento': '33333333',
                'estado': 'Rechazado',  # Este NO debe recibir certificado
                'first_name': 'Miguel',
                'last_name': 'Torres'
            }
        ]
        
        self.evaluadores_admitidos = []
        for evaluador_data in self.evaluadores_data:
            # Crear usuario evaluador
            user_evaluador = User.objects.create_user(
                username=evaluador_data['username'],
                email=evaluador_data['email'],
                password='testpass123',
                tipo_documento='CC',
                documento_identidad=evaluador_data['documento'],
                first_name=evaluador_data['first_name'],
                last_name=evaluador_data['last_name']
            )
            
            # Crear perfil de evaluador
            evaluador = Evaluadores.objects.create(usuario=user_evaluador)
            
            # Crear relación con evento usando timezone-aware datetime
            EvaluadoresEventos.objects.create(
                eva_eve_evaluador_fk=evaluador,
                eva_eve_evento_fk=self.evento,
                eva_estado=evaluador_data['estado'],
                # Agregar otros campos requeridos del modelo EvaluadoresEventos si existen
            )
            
            if evaluador_data['estado'] == 'Admitido':
                self.evaluadores_admitidos.append(evaluador)

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
        
        # Probar con POST (el método que realmente usa la vista)
        response = self.client.post(url)
        
        # Debería redirigir a login o denegar acceso
        self.assertNotEqual(response.status_code, 200, "Vista debería requerir autenticación")
        self.assertIn(response.status_code, [302, 403, 401])

    def test_acceso_vista_con_autenticacion(self):
        """Prueba el comportamiento de la vista con administradores autenticados"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
        
        # POST debería ser aceptado (redirección 302)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302, "POST debería redirigir después del envío")

    def test_envio_certificados_todos_evaluadores_admitidos(self):
        """Prueba que se envíen certificados a TODOS los evaluadores admitidos"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            # Mock para simular la generación de PDF
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
            
            # Realizar petición POST para enviar certificados
            response = self.client.post(url)
            
            # Verificar redirección exitosa
            self.assertEqual(response.status_code, 302, 
                           f"Se esperaba redirección 302 pero se obtuvo {response.status_code}")
            
            # Verificar que se enviaron correos a TODOS los evaluadores admitidos
            expected_emails = 2  # 2 evaluadores admitidos
            self.assertEqual(len(mail.outbox), expected_emails,
                            f"Se esperaban {expected_emails} correos, se enviaron {len(mail.outbox)}")
            
            # Verificar que los correos llegaron a los emails correctos
            emails_enviados = [correo.to[0] for correo in mail.outbox]
            expected_emails_list = ['evaluador1@test.com', 'evaluador2@test.com']
            self.assertEqual(sorted(emails_enviados), sorted(expected_emails_list))

    def test_contenido_correos_evaluadores(self):
        """Prueba el contenido de los correos enviados a evaluadores"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
            
            # Realizar petición POST
            response = self.client.post(url)
            
            # Verificar que se enviaron correos
            self.assertGreater(len(mail.outbox), 0, "No se enviaron correos")
            
            # Verificar contenido del primer correo
            primer_correo = mail.outbox[0]
            self.assertIn('Certificado de participación', primer_correo.subject)
            self.assertIn(self.evento.eve_nombre, primer_correo.subject)
            self.assertEqual(primer_correo.from_email, settings.DEFAULT_FROM_EMAIL)
            
            # Verificar que el correo es HTML
            self.assertEqual(primer_correo.content_subtype, 'html')
            
            # Verificar que tiene adjunto PDF
            self.assertEqual(len(primer_correo.attachments), 1)
            adjunto = primer_correo.attachments[0]
            self.assertIn('.pdf', adjunto[0])
            self.assertIn('certificado_', adjunto[0])
            self.assertEqual(adjunto[2], 'application/pdf')

    def test_no_envio_evaluadores_no_admitidos(self):
        """Prueba que NO se envíen certificados a evaluadores no admitidos"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
            self.client.post(url)
            
            # Verificar que NO se envió correo al evaluador rechazado
            correos_enviados = [correo.to[0] for correo in mail.outbox]
            self.assertNotIn('evaluador3@test.com', correos_enviados)

    def test_estructura_consulta_evaluadores_admitidos(self):
        """Prueba que la consulta filtre correctamente solo evaluadores admitidos"""
        # Verificar directamente en el modelo
        evaluadores_admitidos_db = Evaluadores.objects.filter(
            id__in=EvaluadoresEventos.objects.filter(
                eva_eve_evento_fk=self.evento.id,
                eva_estado__iexact='Admitido'
            ).values_list('eva_eve_evaluador_fk_id', flat=True)
        )
        
        self.assertEqual(evaluadores_admitidos_db.count(), 2)
        
        # Verificar que los evaluadores admitidos son los correctos
        evaluadores_emails = [e.usuario.email for e in evaluadores_admitidos_db]
        self.assertIn('evaluador1@test.com', evaluadores_emails)
        self.assertIn('evaluador2@test.com', evaluadores_emails)
        self.assertNotIn('evaluador3@test.com', evaluadores_emails)

    def test_nombres_archivos_adjuntos_evaluadores(self):
        """Prueba que los archivos adjuntos tengan nombres correctos con documentos de identidad"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_evaluadores', args=[self.evento.id])
            self.client.post(url)
            
            # Verificar nombres de archivos adjuntos
            documentos_en_adjuntos = []
            for correo in mail.outbox:
                adjunto = correo.attachments[0]
                nombre_archivo = adjunto[0]
                self.assertIn('certificado_', nombre_archivo)
                self.assertTrue(nombre_archivo.endswith('.pdf'))
                
                # Extraer documento del nombre de archivo
                doc = nombre_archivo.replace('certificado_', '').replace('.pdf', '')
                documentos_en_adjuntos.append(doc)
            
            # Verificar que están los documentos de los evaluadores admitidos
            expected_docs = ['11111111', '22222222']
            self.assertEqual(sorted(documentos_en_adjuntos), sorted(expected_docs))

