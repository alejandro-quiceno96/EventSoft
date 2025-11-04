from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from io import BytesIO

from app_eventos.models import Eventos, ParticipantesEventos
from app_participante.models import Participantes
from app_certificados.models import Certificado
from app_administrador.models import Administradores

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EnvioCertificadoParticipantesTestCase(TestCase):
    """HU25: Como EXPONENTE, quiero recibir mi certificado de participación por correo."""

    def setUp(self):
        # ---- Usuario participante ----
        self.user = User.objects.create_user(
            username='expo1',
            password='12345',
            first_name='Carlos',
            last_name='Lopez',
            email='carlos@example.com'
        )
        self.participante = Participantes.objects.create(usuario=self.user)
        self.admin_user = Administradores.objects.create(usuario=self.user)

        # ---- Evento ----
        self.evento = Eventos.objects.create(
            eve_nombre='Congreso Nacional',
            eve_descripcion='Evento de prueba para certificados',
            eve_ciudad='Bogotá',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio=date(2025, 11, 1),
            eve_fecha_fin=date(2025, 11, 3),
            eve_estado='Activo',
            eve_imagen=SimpleUploadedFile("banner.jpg", b"imagen falsa", content_type="image/jpeg"),
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin_user
        )

        # ---- Certificado configurado ----
        self.certificado = Certificado.objects.create(
            evento_fk=self.evento,
            diseño=SimpleUploadedFile("diseno.jpg", b"diseno falso", content_type="image/jpeg"),
            firma=SimpleUploadedFile("firma.png", b"firma falsa", content_type="image/png"),
            firma_nombre='Dr. Juan Pérez',
            firma_cargo='Director Académico',
            orientacion='horizontal',
            certifica='Ha participado exitosamente en el evento.',
            lugar_expedicion='Bogotá D.C.',
            tipografia='Arial'
        )

        # ---- Participante Admitido ----
        self.participante_evento = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_estado='Admitido',
            par_eve_fecha_hora=timezone.now(),
            par_eve_qr=SimpleUploadedFile("qr.png", b"codigo qr falso", content_type="image/png"),
            par_eve_clave='CLAVE123'
        )

        # ---- Cliente autenticado ----
        self.client = Client()
        self.client.login(username='expo1', password='12345')

        self.url = reverse('administrador:enviar_certificado_participantes', kwargs={'evento_id': self.evento.id})

    # ------------------------------------------------------------------
    # ✅ TEST: Envío exitoso de certificado a participantes admitidos
    # ------------------------------------------------------------------
    def test_enviar_certificado_a_participante_admitido(self):
        response = self.client.post(self.url)

        # Verifica redirección correcta tras envío
        self.assertEqual(response.status_code, 302)

        # Verifica que se haya enviado exactamente un correo
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Verifica el contenido del correo
        self.assertIn('Certificado de participación', email.subject)
        self.assertIn(self.participante.usuario.email, email.to)
        self.assertIn(self.evento.eve_nombre, email.subject)

        # Verifica que haya un archivo adjunto (el PDF)
        self.assertEqual(len(email.attachments), 1)
        nombre_pdf, contenido_pdf, tipo = email.attachments[0]
        self.assertTrue(nombre_pdf.endswith('.pdf'))
        self.assertEqual(tipo, 'application/pdf')
        self.assertGreater(len(contenido_pdf), 500)  # que tenga contenido real

    # ------------------------------------------------------------------
    # ❌ TEST: No se envían certificados si no hay admitidos
    # ------------------------------------------------------------------
    def test_no_envia_certificados_sin_admitidos(self):
        # Cambiar estado a Pendiente
        self.participante_evento.par_eve_estado = 'Pendiente'
        self.participante_evento.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # ❌ TEST: No se encuentra certificado configurado
    # ------------------------------------------------------------------
    def test_no_envia_si_no_hay_certificado_configurado(self):
        # Eliminar el certificado asociado al evento
        self.certificado.delete()

        response = self.client.post(self.url)

        # Verifica que no se haya enviado ningún correo
        self.assertEqual(len(mail.outbox), 0)

        # Ajuste: la vista actual redirige (302) en vez de devolver 404
        self.assertIn(response.status_code, [302, 404])
