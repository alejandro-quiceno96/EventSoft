import datetime
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse

from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_participante.models import Participantes
from app_administrador.models import Administradores
from app_certificados.models import Certificado
from app_usuarios.models import Usuario  # Asegúrate de ajustar al nombre real de tu app de usuarios


class EnviarCertificadoReconocimientoTestCase(TestCase):
    """Pruebas automatizadas para HU27 - Envío de certificado de reconocimiento."""

    def setUp(self):
        self.client = Client()

        # ---- Crear usuario administrador ----
        self.admin_usuario = Usuario.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            tipo_documento='CC',
            documento_identidad='999999',
        )
        self.admin = Administradores.objects.create(usuario=self.admin_usuario)

        # ---- Crear evento ----
        self.evento = Eventos.objects.create(
            eve_nombre='Expo Innovación 2025',
            eve_descripcion='Evento de prueba',
            eve_ciudad='Bogotá',
            eve_lugar='Corferias',
            eve_fecha_inicio=datetime.date.today(),
            eve_fecha_fin=datetime.date.today() + datetime.timedelta(days=1),
            eve_estado='Activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        # ---- Crear usuarios participantes ----
        # ---- Crear usuarios participantes ----
        self.user1 = Usuario.objects.create_user(
            username='expo1',
            email='ganador@example.com',
            password='test123',
            first_name='Juan',
            last_name='Pérez',
            tipo_documento='CC',
            documento_identidad='12345',
            segundo_nombre=''  
        )

        self.user2 = Usuario.objects.create_user(
            username='expo2',
            email='participante@example.com',
            password='test123',
            first_name='Ana',
            last_name='López',
            tipo_documento='CC',
            documento_identidad='67890',
            segundo_nombre=''
        )
        
        self.certificado = Certificado.objects.create(
        evento_fk=self.evento,
        diseño=SimpleUploadedFile(
            name='test_diseño.png',
            content=b'',  # contenido vacío solo para pruebas
            content_type='image/png'
        ),)


        # ---- Crear participantes ----
        self.participante1 = Participantes.objects.create(usuario=self.user1)
        self.participante2 = Participantes.objects.create(usuario=self.user2)

        # ---- Crear proyectos ----
        self.proyecto1 = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo='P001',
            pro_nombre='Proyecto Ganador',
            pro_descripcion='Proyecto con primer lugar',
            pro_documentos=SimpleUploadedFile('proyecto1.pdf', b'data'),
            pro_estado='Aprobado',
            pro_calificación_final=98.0
        )

        self.proyecto2 = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo='P002',
            pro_nombre='Proyecto Finalista',
            pro_descripcion='Proyecto sin puesto destacado',
            pro_documentos=SimpleUploadedFile('proyecto2.pdf', b'data'),
            pro_estado='Aprobado',
            pro_calificación_final=85.0
        )

        # ---- Crear relaciones ParticipantesEventos ----
        self.par_eve1 = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante1,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=datetime.datetime.now(),
            par_eve_documentos=SimpleUploadedFile('doc1.pdf', b'data'),
            par_eve_estado='Activo',
            par_eve_qr=SimpleUploadedFile('qr1.pdf', b'data'),
            par_eve_clave='clave1',
            par_eve_calificacion_final=98.0,
            par_eve_proyecto=self.proyecto1
        )

        self.par_eve2 = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante2,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=datetime.datetime.now(),
            par_eve_documentos=SimpleUploadedFile('doc2.pdf', b'data'),
            par_eve_estado='Activo',
            par_eve_qr=SimpleUploadedFile('qr2.pdf', b'data'),
            par_eve_clave='clave2',
            par_eve_calificacion_final=85.0,
            par_eve_proyecto=self.proyecto2
        )

        # ---- Configurar URL de la vista ----
        self.url = reverse('administrador:enviar_certificado_reconocimiento', args=[self.evento.id, self.proyecto1.id])
        self.client.login(username='admin', password='admin123')

    # ============================================================
    # ✅ Criterio 1: Solo se envía certificado al proyecto ganador
    # ============================================================
    @patch('app_administrador.utils.generar_reconocmiento', return_value=b"PDF CONTENT")
    def test_envio_certificado_solo_al_participante_ganador(self, mock_pdf):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(self.user1.email, email.to)
        self.assertNotIn(self.user2.email, email.to)


    # ============================================================
    # ✅ Criterio 2: Solo se permite método POST
    # ============================================================
    def test_no_se_permite_metodo_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('Método no permitido', response.json()['message'])
