from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, ParticipantesEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from unittest.mock import patch
from django.conf import settings
from app_certificados.models import Certificado
from datetime import datetime
from app_participante.models import Participantes


class EnviarCertificadoParticipantesTestCase(TestCase):
    
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
            eve_nombre='Evento Test Participantes',
            eve_descripcion='Descripción del evento test para participantes',
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
            certifica='Por haber participado como expositor en el evento',
            lugar_expedicion='Bogotá, D.C.',
            tipografia='Arial',
            diseño=SimpleUploadedFile("diseño.png", b"file_content"),
            firma=SimpleUploadedFile("firma.png", b"file_content")
        )
        
        # Crear participantes y sus relaciones con el evento
        self.participantes_data = [
            {
                'username': 'participante1',
                'email': 'participante1@test.com',
                'documento': '11111111',
                'estado': 'Admitido',
                'first_name': 'Ana',
                'last_name': 'Rodríguez'
            },
            {
                'username': 'participante2', 
                'email': 'participante2@test.com',
                'documento': '22222222',
                'estado': 'Admitido',
                'first_name': 'Luis',
                'last_name': 'Martínez'
            },
            {
                'username': 'participante3',
                'email': 'participante3@test.com', 
                'documento': '33333333',
                'estado': 'Rechazado',  # Este NO debe recibir certificado
                'first_name': 'Pedro',
                'last_name': 'García'
            }
        ]
        
        self.participantes_admitidos = []
        for participante_data in self.participantes_data:
            # Crear usuario participante
            user_participante = User.objects.create_user(
                username=participante_data['username'],
                email=participante_data['email'],
                password='testpass123',
                tipo_documento='CC',
                documento_identidad=participante_data['documento'],
                first_name=participante_data['first_name'],
                last_name=participante_data['last_name']
            )
            
            # Crear perfil de participante
            participante = Participantes.objects.create(usuario=user_participante)
            
            # Crear relación con evento (con todos los campos requeridos)
            ParticipantesEventos.objects.create(
                par_eve_participante_fk=participante,
                par_eve_evento_fk=self.evento,
                par_eve_fecha_hora=datetime.now(),
                par_eve_documentos=SimpleUploadedFile("proyecto.pdf", b"file_content"),
                par_eve_estado=participante_data['estado'],
                par_eve_qr=SimpleUploadedFile("qr.pdf", b"file_content"),
                par_eve_clave='CLAVE456',
                par_eve_calificacion_final=4.5,
                habilitado=True
            )
            
            if participante_data['estado'] == 'Admitido':
                self.participantes_admitidos.append(participante)

    def test_acceso_vista_sin_autenticacion(self):
            """Prueba que la vista requiera autenticación"""
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
            
            # Probar con POST (el método que realmente usa la vista)
            response = self.client.post(url)
            
            # Debería redirigir a login o denegar acceso
            self.assertNotEqual(response.status_code, 200, "Vista debería requerir autenticación")
            self.assertIn(response.status_code, [302, 403, 401])

    def test_acceso_vista_con_autenticacion(self):
        """Prueba el comportamiento de la vista con administradores autenticados"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
        
        # GET debería retornar 405 (Method Not Allowed)
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 405, "GET debería retornar 405 Method Not Allowed")
        
        # POST debería ser aceptado
        response_post = self.client.post(url)
        self.assertNotEqual(response_post.status_code, 405, "POST debería ser aceptado")

    def test_envio_certificados_todos_participantes_admitidos(self):
        """Prueba que se envíen certificados a TODOS los participantes admitidos"""
        with patch('app_administrador.utils.generar_certificados_expositores') as mock_generar:
            # Mock para simular la generación de PDF
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
            
            # Realizar petición POST para enviar certificados
            response = self.client.post(url)
            
            # Verificar redirección exitosa
            self.assertEqual(response.status_code, 302, 
                           f"Se esperaba redirección 302 pero se obtuvo {response.status_code}")
            
            # Verificar que se enviaron correos a TODOS los participantes admitidos
            expected_emails = 2  # 2 participantes admitidos
            self.assertEqual(len(mail.outbox), expected_emails,
                            f"Se esperaban {expected_emails} correos, se enviaron {len(mail.outbox)}")
            
            # Verificar que los correos llegaron a los emails correctos
            emails_enviados = [correo.to[0] for correo in mail.outbox]
            expected_emails_list = ['participante1@test.com', 'participante2@test.com']
            self.assertEqual(sorted(emails_enviados), sorted(expected_emails_list))

    def test_contenido_correos_participantes(self):
        """Prueba el contenido de los correos enviados a participantes"""
        with patch('app_administrador.utils.generar_certificados_expositores') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
            
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

    def test_no_envio_participantes_no_admitidos(self):
        """Prueba que NO se envíen certificados a participantes no admitidos"""
        with patch('app_administrador.utils.generar_certificados_expositores') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
            self.client.post(url)
            
            # Verificar que NO se envió correo al participante rechazado
            correos_enviados = [correo.to[0] for correo in mail.outbox]
            self.assertNotIn('participante3@test.com', correos_enviados)

    def test_estructura_consulta_participantes_admitidos(self):
        """Prueba que la consulta filtre correctamente solo participantes admitidos"""
        # Verificar directamente en el modelo
        participantes_admitidos_db = Participantes.objects.filter(
            id__in=ParticipantesEventos.objects.filter(
                par_eve_evento_fk=self.evento.id,
                par_eve_estado__iexact='Admitido'
            ).values_list('par_eve_participante_fk_id', flat=True)
        )
        
        self.assertEqual(participantes_admitidos_db.count(), 2)
        
        # Verificar que los participantes admitidos son los correctos
        participantes_emails = [p.usuario.email for p in participantes_admitidos_db]
        self.assertIn('participante1@test.com', participantes_emails)
        self.assertIn('participante2@test.com', participantes_emails)
        self.assertNotIn('participante3@test.com', participantes_emails)

    def test_nombres_archivos_adjuntos_participantes(self):
        """Prueba que los archivos adjuntos tengan nombres correctos con documentos de identidad"""
        with patch('app_administrador.utils.generar_certificados_expositores') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
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
            
            # Verificar que están los documentos de los participantes admitidos
            expected_docs = ['11111111', '22222222']
            self.assertEqual(sorted(documentos_en_adjuntos), sorted(expected_docs))

    def test_manejo_errores_generacion_pdf(self):
        """Prueba que la vista maneje correctamente errores en la generación de PDF"""
        with patch('app_administrador.utils.generar_certificados_expositores') as mock_generar:
            # Simular que la generación de PDF retorna HttpResponse (error)
            from django.http import HttpResponse
            mock_generar.return_value = HttpResponse("Error en generación de PDF", status=400)
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_participantes', args=[self.evento.id])
            
            # La vista debería continuar sin caerse
            response = self.client.post(url)
            
            # Verificar que se procesó la petición
            self.assertEqual(response.status_code, 302)

