from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from app_participante.models import Participantes
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, ParticipantesEventos, Proyecto
from app_administrador.models import Administradores
from django.utils import timezone
from datetime import timedelta
from django.test import Client

class PreinscripcionExponenteTest(TestCase):
    def setUp(self):
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            password="testpass123",
            tipo_documento="CC",
            documento_identidad="99999999"
        )
        self.client.login(username="admin_test", password="testpass123")
        self.admin = Administradores.objects.create(usuario=self.usuario_admin)

        # Evento con costo
        self.evento = Eventos.objects.create(
            eve_nombre="Evento con Costo",
            eve_descripcion="Evento que requiere pago",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="Activo",
            eve_imagen="image/evento_pago.png",
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin,
            eve_programacion="pdf/programacion/evento_pago.pdf"
        )
        
        
    def test_envio_exitoso_con_pdf(self):
        # Archivo de prueba
        archivo = SimpleUploadedFile(
            "proyecto.pdf", b"contenido del PDF", content_type="application/pdf"
        )

        # URL del endpoint
        url = reverse("submit_preinscripcion_participante")

        # POST con evento_id como entero y archivo
        response = self.client.post(url, {
            "pro_nombre": "Proyecto A",
            "pro_descripcion": "Descripcion de prueba",
            "pro_documentos": archivo,
            "evento_id": self.evento.id,   # <-- importante: solo el ID
            "opcion": "inscribir",
        })

        # Verificar redirección
        self.assertRedirects(
            response,
            reverse("inicio_visitante") + "?registro=exito_participante"
        )

        # Verificar que la inscripción se haya creado correctamente
        inscripcion = ParticipantesEventos.objects.first()
        self.assertIsNotNone(inscripcion)
        self.assertEqual(inscripcion.par_eve_estado, "Pendiente")
        proyecto = Proyecto.objects.first()
        self.assertIsNotNone(proyecto)
        self.assertEqual(proyecto.pro_nombre, "Proyecto A")
        self.assertEqual(proyecto.pro_estado, "Pendiente")

    def test_falla_sin_documento(self):
        """Si no se adjunta documento obligatorio, debe mostrar error y no crear inscripción"""
        # Asegurarse de que el usuario esté logueado
        self.client.login(username= "admin_test", password="testpass123")

        # Hacer POST sin archivo
        response = self.client.post(
            reverse("submit_preinscripcion_participante"),
            {
                "pro_nombre": "Proyecto B",
                "pro_descripcion": "Descripción del proyecto",
                "evento_id": self.evento.id,
                "opcion": "inscribir",
                # pro_documentos NO se envía
            }
        )

        # Validar que retorna 200 (render del formulario nuevamente)
        self.assertRedirects(
            response, reverse("detalle_evento", args=[self.evento.id]))

        # Validar que NO se creó ninguna inscripción
        self.assertFalse(
            ParticipantesEventos.objects.filter(par_eve_evento_fk=self.evento).exists()
    )

