from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes
from app_usuarios.models import Usuario as User
from unittest.mock import patch
from django.conf import settings
from app_certificados.models import Certificado


class EnviarCertificadoAsistentesTestCase(TestCase):
    
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
            eve_nombre='Evento Test Certificados',
            eve_descripcion='Descripción del evento test',
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
            certifica='Por haber participado exitosamente en el evento',
            lugar_expedicion='Bogotá, D.C.',
            tipografia='Arial',
            diseño=SimpleUploadedFile("diseño.png", b"file_content"),
            firma=SimpleUploadedFile("firma.png", b"file_content")
        )
        
        # Crear asistentes y sus relaciones con el evento
        self.asistentes_data = [
            {
                'username': 'asistente1',
                'email': 'asistente1@test.com',
                'documento': '11111111',
                'estado': 'Admitido',
                'first_name': 'Juan',
                'last_name': 'Pérez'
            },
            {
                'username': 'asistente2', 
                'email': 'asistente2@test.com',
                'documento': '22222222',
                'estado': 'Admitido',
                'first_name': 'María',
                'last_name': 'Gómez'
            },
            {
                'username': 'asistente3',
                'email': 'asistente3@test.com', 
                'documento': '33333333',
                'estado': 'Rechazado',  # Este NO debe recibir certificado
                'first_name': 'Carlos',
                'last_name': 'López'
            }
        ]
        
        self.asistentes_admitidos = []
        for asistente_data in self.asistentes_data:
            # Crear usuario asistente
            user_asistente = User.objects.create_user(
                username=asistente_data['username'],
                email=asistente_data['email'],
                password='testpass123',
                tipo_documento='CC',
                documento_identidad=asistente_data['documento'],
                first_name=asistente_data['first_name'],
                last_name=asistente_data['last_name']
            )
            
            # Crear perfil de asistente
            asistente = Asistentes.objects.create(usuario=user_asistente)
            
            # Crear relación con evento
            AsistentesEventos.objects.create(
                asi_eve_asistente_fk=asistente,
                asi_eve_evento_fk=self.evento,
                asi_eve_estado=asistente_data['estado'],
                asi_eve_soporte=SimpleUploadedFile("soporte.pdf", b"file_content"),
                asi_eve_qr=SimpleUploadedFile("qr.pdf", b"file_content"),
                asi_eve_clave='CLAVE123'
            )
            
            if asistente_data['estado'] == 'Admitido':
                self.asistentes_admitidos.append(asistente)

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_acceso_vista_con_autenticacion(self):
        """Prueba que la vista sea accesible para administradores autenticados"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vista de envío de certificados lista para ejecutar")

    def test_envio_certificados_todos_asistentes_admitidos(self):
        """Prueba que se envíen certificados a TODOS los asistentes admitidos"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
        
        # Realizar petición POST para enviar certificados
        response = self.client.post(url)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302, 
                    f"Se esperaba redirección 302 pero se obtuvo {response.status_code}")
        
        # Verificar que se enviaron correos a TODOS los asistentes admitidos
        expected_emails = 2  # 2 asistentes admitidos
        self.assertEqual(len(mail.outbox), expected_emails,
                        f"Se esperaban {expected_emails} correos, se enviaron {len(mail.outbox)}")
        
        # Verificar que los correos llegaron a los emails correctos
        emails_enviados = [correo.to[0] for correo in mail.outbox]
        expected_emails_list = ['asistente1@test.com', 'asistente2@test.com']
        self.assertEqual(sorted(emails_enviados), sorted(expected_emails_list))

    def test_contenido_correos_enviados(self):
        """Prueba el contenido de los correos enviados"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
            
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

    def test_no_envio_asistentes_no_admitidos(self):
        """Prueba que NO se envíen certificados a asistentes no admitidos"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
            self.client.post(url)
            
            # Verificar que NO se envió correo al asistente rechazado
            correos_enviados = [correo.to[0] for correo in mail.outbox]
            self.assertNotIn('asistente3@test.com', correos_enviados)

    def test_estructura_consulta_asistentes_admitidos(self):
        """Prueba que la consulta filtre correctamente solo asistentes admitidos"""
        # Verificar directamente en el modelo
        asistentes_admitidos_db = Asistentes.objects.filter(
            id__in=AsistentesEventos.objects.filter(
                asi_eve_evento_fk=self.evento.id,
                asi_eve_estado__iexact='Admitido'
            ).values_list('asi_eve_asistente_fk_id', flat=True)
        )
        
        self.assertEqual(asistentes_admitidos_db.count(), 2)
        
        # Verificar que los asistentes admitidos son los correctos
        asistentes_emails = [a.usuario.email for a in asistentes_admitidos_db]
        self.assertIn('asistente1@test.com', asistentes_emails)
        self.assertIn('asistente2@test.com', asistentes_emails)
        self.assertNotIn('asistente3@test.com', asistentes_emails)

    def test_nombres_archivos_adjuntos(self):
        """Prueba que los archivos adjuntos tengan nombres correctos con documentos de identidad"""
        with patch('app_administrador.utils.generar_certificados') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_asistentes', args=[self.evento.id])
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
            
            # Verificar que están los documentos de los asistentes admitidos
            expected_docs = ['11111111', '22222222']
            self.assertEqual(sorted(documentos_en_adjuntos), sorted(expected_docs))


