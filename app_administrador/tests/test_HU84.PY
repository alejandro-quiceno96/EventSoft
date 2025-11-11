from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.http import JsonResponse
from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
from unittest.mock import patch
from django.conf import settings
from app_certificados.models import Certificado
from app_participante.models import Participantes


class EnviarCertificadoReconocimientoTestCase(TestCase):
    
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
            eve_nombre='Evento Test Reconocimiento',
            eve_descripcion='Descripción del evento test para reconocimientos',
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
        
        # Crear proyecto relacionado con el evento
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo='PROY001',
            pro_nombre='Proyecto Ganador Test',
            pro_descripcion='Descripción del proyecto ganador',
            pro_documentos=SimpleUploadedFile("proyecto_doc.pdf", b"file_content"),
            pro_estado='Aprobado',
            pro_calificación_final=4.8  # Alta calificación para reconocimiento
        )
        
        # Crear participantes y sus relaciones con el evento y proyecto
        self.participantes_data = [
            {
                'username': 'participante1',
                'email': 'participante1@test.com',
                'documento': '11111111',
                'first_name': 'Ana',
                'last_name': 'Rodríguez'
            },
            {
                'username': 'participante2', 
                'email': 'participante2@test.com',
                'documento': '22222222',
                'first_name': 'Luis',
                'last_name': 'Martínez'
            }
        ]
        
        self.participantes_reconocidos = []
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
            self.participantes_reconocidos.append(participante)
            
            # Crear relación con evento y proyecto
            ParticipantesEventos.objects.create(
                par_eve_participante_fk=participante,
                par_eve_evento_fk=self.evento,
                par_eve_fecha_hora=timezone.now(),
                par_eve_documentos=SimpleUploadedFile("proyecto.pdf", b"file_content"),
                par_eve_estado='Admitido',
                par_eve_qr=SimpleUploadedFile("qr.pdf", b"file_content"),
                par_eve_clave='CLAVE456',
                par_eve_calificacion_final=4.8,
                par_eve_proyecto=self.proyecto,
                habilitado=True
            )

    def test_acceso_vista_sin_autenticacion(self):
        """Prueba que la vista requiera autenticación"""
        url = reverse('administrador:enviar_certificado_reconocimiento', 
                     args=[self.evento.id, self.proyecto.id])
        
        # Probar con POST (el método que realmente usa la vista)
        response = self.client.post(url)
        
        # Debería redirigir a login o denegar acceso
        self.assertNotEqual(response.status_code, 200, "Vista debería requerir autenticación")
        self.assertIn(response.status_code, [302, 403, 401])

    def test_acceso_vista_con_autenticacion_metodo_post(self):
        """Prueba que la vista acepte método POST con autenticación"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_reconocimiento', 
                     args=[self.evento.id, self.proyecto.id])
        
        # POST debería ser aceptado
        with patch('app_administrador.utils.generar_reconocmiento') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            response = self.client.post(url)
            
            # Debería retornar JsonResponse con success=True
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json')
            
            # Verificar contenido de la respuesta JSON
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Reconocimiento enviado correctamente.')

    def test_metodo_get_no_permitido(self):
        """Prueba que GET retorne método no permitido"""
        self.client.login(username='admin_test', password='testpass123')
        url = reverse('administrador:enviar_certificado_reconocimiento', 
                     args=[self.evento.id, self.proyecto.id])
        
        response = self.client.get(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Método no permitido.')

    def test_envio_certificados_reconocimiento_participantes_proyecto(self):
        """Prueba que se envíen certificados de reconocimiento a TODOS los participantes del proyecto"""
        with patch('app_administrador.utils.generar_reconocmiento') as mock_generar:
            # Mock para simular la generación de PDF
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_reconocimiento', 
                         args=[self.evento.id, self.proyecto.id])
            
            # Realizar petición POST para enviar reconocimientos
            response = self.client.post(url)
            
            # Verificar respuesta JSON exitosa
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            
            # Verificar que se enviaron correos a TODOS los participantes del proyecto
            expected_emails = 2  # 2 participantes en el proyecto
            self.assertEqual(len(mail.outbox), expected_emails,
                            f"Se esperaban {expected_emails} correos, se enviaron {len(mail.outbox)}")
            
            # Verificar que los correos llegaron a los emails correctos
            emails_enviados = [correo.to[0] for correo in mail.outbox]
            expected_emails_list = ['participante1@test.com', 'participante2@test.com']
            self.assertEqual(sorted(emails_enviados), sorted(expected_emails_list))

    def test_contenido_correos_reconocimiento(self):
        """Prueba el contenido de los correos de reconocimiento"""
        with patch('app_administrador.utils.generar_reconocmiento') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_reconocimiento', 
                         args=[self.evento.id, self.proyecto.id])
            
            # Realizar petición POST
            response = self.client.post(url)
            
            # Verificar que se enviaron correos
            self.assertGreater(len(mail.outbox), 0, "No se enviaron correos")
            
            # Verificar contenido del primer correo
            primer_correo = mail.outbox[0]
            self.assertIn('Reconocimiento en el evento', primer_correo.subject)
            self.assertIn(self.evento.eve_nombre, primer_correo.subject)
            self.assertEqual(primer_correo.from_email, settings.DEFAULT_FROM_EMAIL)
            
            # Verificar que el correo es HTML
            self.assertEqual(primer_correo.content_subtype, 'html')
            
            # Verificar que tiene adjunto PDF
            self.assertEqual(len(primer_correo.attachments), 1)
            adjunto = primer_correo.attachments[0]
            self.assertIn('.pdf', adjunto[0])
            self.assertIn('Reconocmiento_', adjunto[0])  # Nota: hay typo en "Reconocmiento"
            self.assertEqual(adjunto[2], 'application/pdf')

    def test_estructura_consulta_participantes_proyecto(self):
        """Prueba que la consulta encuentre correctamente los participantes del proyecto"""
        # Verificar directamente en el modelo
        participantes_proyecto_db = ParticipantesEventos.objects.filter(
            par_eve_proyecto=self.proyecto.id,
            par_eve_evento_fk=self.evento.id
        )
        
        self.assertEqual(participantes_proyecto_db.count(), 2)
        
        # Verificar que los participantes del proyecto son los correctos
        participantes_emails = [p.par_eve_participante_fk.usuario.email for p in participantes_proyecto_db]
        self.assertIn('participante1@test.com', participantes_emails)
        self.assertIn('participante2@test.com', participantes_emails)

    def test_nombres_archivos_adjuntos_reconocimiento(self):
        """Prueba que los archivos adjuntos tengan nombres correctos con documentos de identidad"""
        with patch('app_administrador.utils.generar_reconocmiento') as mock_generar:
            mock_generar.return_value = b'fake_pdf_content'
            
            self.client.login(username='admin_test', password='testpass123')
            url = reverse('administrador:enviar_certificado_reconocimiento', 
                         args=[self.evento.id, self.proyecto.id])
            self.client.post(url)
            
            # Verificar nombres de archivos adjuntos
            documentos_en_adjuntos = []
            for correo in mail.outbox:
                adjunto = correo.attachments[0]
                nombre_archivo = adjunto[0]
                self.assertIn('Reconocmiento_', nombre_archivo)  # Nota: typo en "Reconocmiento"
                self.assertTrue(nombre_archivo.endswith('.pdf'))
                
                # Extraer documento del nombre de archivo
                doc = nombre_archivo.replace('Reconocmiento_', '').replace('.pdf', '')
                documentos_en_adjuntos.append(doc)
            
            # Verificar que están los documentos de los participantes
            expected_docs = ['11111111', '22222222']
            self.assertEqual(sorted(documentos_en_adjuntos), sorted(expected_docs))

    def test_proyecto_relacionado_con_evento(self):
        """Prueba que el proyecto esté correctamente relacionado con el evento"""
        self.assertEqual(self.proyecto.pro_evento_fk, self.evento)
        self.assertEqual(self.proyecto.pro_codigo, 'PROY001')
        self.assertEqual(self.proyecto.pro_nombre, 'Proyecto Ganador Test')
        self.assertEqual(self.proyecto.pro_calificación_final, 4.8)
