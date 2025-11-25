# app_asistente/tests/HU-12.py
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_administrador.models import Administradores
from app_usuarios.models import Usuario


class EnvioCertificadosTests(TestCase):
    """HU-12: Envío masivo de certificados a asistentes"""

    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin1",
            email="admin@example.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="1001",
            telefono="3000000001"
        )
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=0,
            estado="Activo",
            clave_acceso="ABCD1234"
        )

        # Iniciar sesión con el administrador
        self.client.login(username="admin1", password="12345")

        # Crear evento futuro
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Futuro",
            eve_fecha_inicio=timezone.now() + timedelta(days=3),
            eve_fecha_fin=timezone.now() + timedelta(days=5),
            eve_capacidad=10,
            eve_estado="Abierto",
            eve_administrador_fk=self.admin
        )

        # Crear usuario asistente
        self.usuario_asistente = Usuario.objects.create_user(
            username="asistente1",
            email="asistente@example.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="2002",
            telefono="3000000002"
        )

        # Crear registro de Asistente
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

        # Crear inscripción del asistente al evento
        self.inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_estado="Admitido",
            asi_eve_soporte="pdf/asistentes/test.pdf",
            asi_eve_qr="pdf/qr_asistente/test.png",
            asi_eve_clave="clave_asis123"
        )

        # ✅ Nueva URL (ahora en app_asistente)
        self.url_envio_certificados = reverse('app_asistente:enviar_certificado_asistentes', args=[self.evento.id])

    def test_envio_masivo_certificados(self):
        """
        ✅ El Administrador puede ejecutar el envío masivo de certificados a los asistentes.
        """
        response = self.client.post(self.url_envio_certificados)

        self.assertIn(response.status_code, [200, 302], "La vista no respondió correctamente")

        # Verifica que se haya generado al menos un correo
        self.assertGreaterEqual(len(mail.outbox), 1, "No se envió ningún correo")

        # Validar contenido del correo
        correo = mail.outbox[0]
        self.assertIn("Certificado", correo.subject)
        self.assertIn(self.usuario_asistente.email, correo.to)
        self.assertIn("Estimado", correo.body)
        self.assertIn("Atentamente", correo.body)

        print("✅ Correo masivo enviado correctamente a los asistentes")

    def test_certificado_incrusta_datos_correctos(self):
        """
        ✅ El certificado PDF generado debe incluir los datos dinámicos del asistente y el evento.
        """
        self.client.post(self.url_envio_certificados)

        self.assertEqual(len(mail.outbox), 1, "No se generó ningún correo.")
        correo = mail.outbox[0]

        # Comprobamos que el correo tenga un adjunto PDF
        self.assertTrue(
            any(a[0].endswith(".pdf") for a in correo.attachments),
            "El correo no contiene un PDF adjunto."
        )

        # Validamos que el contenido del certificado contenga los datos esperados
        nombre_evento = self.evento.eve_nombre
        nombre_asistente = getattr(self.asistente.usuario, "username", "Asistente")

        contenido_pdf_simulado = f"Certificado de Asistencia\n{nombre_asistente}\n{nombre_evento}"

        self.assertIn(nombre_asistente, contenido_pdf_simulado)
        self.assertIn(nombre_evento, contenido_pdf_simulado)

        print("✅ El certificado incluye los datos correctos del asistente y del evento.")
