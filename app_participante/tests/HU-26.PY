from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_participante.models import Participantes 
from app_usuarios.models import Usuario
from app_evaluador.models import Evaluadores, Calificaciones
from app_criterios.models import Criterios
from app_administrador.models import Administradores


class HU26VerCalificacionesParticipanteTestCase(TestCase):
    """Pruebas automatizadas para HU26: Ver calificación, puntaje y observaciones del participante."""

    def setUp(self):
        self.client = Client()

        # --- Crear usuario y participante ---
        self.usuario_participante = Usuario.objects.create_user(
            username="alejo123",
            password="testpass",
            first_name="Alejandro",
            last_name="Pérez",
            documento_identidad="123456789",
        )
        self.participante = Participantes.objects.create(usuario=self.usuario_participante)

        # --- Crear administrador (requerido por Eventos) ---
        self.usuario_admin = Usuario.objects.create_user(
            username="admin1",
            password="adminpass",
            first_name="Laura",
            last_name="Gómez",
            documento_identidad="987654321",
        )
        self.admin = Administradores.objects.create(usuario=self.usuario_admin)

        # --- Crear archivo simulado para imagen y documentos ---
        imagen = SimpleUploadedFile("evento.jpg", b"fakeimagecontent", content_type="image/jpeg")
        doc = SimpleUploadedFile("archivo.pdf", b"fakepdfcontent", content_type="application/pdf")

        # --- Crear evento con todos los campos obligatorios ---
        self.evento = Eventos.objects.create(
            eve_nombre="Feria Nacional de Ciencia",
            eve_descripcion="Evento académico y científico nacional",
            eve_ciudad="Bogotá",
            eve_lugar="Corferias",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Activo",
            eve_imagen=imagen,
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        # --- Crear proyecto ---
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PRJ001",
            pro_nombre="Sistema Solar Inteligente",
            pro_descripcion="Proyecto de energía limpia e innovación",
            pro_documentos=doc,
            pro_estado="Aprobado"
        )

        # --- Relación Participante-Evento ---
        self.participante_evento = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=doc,
            par_eve_estado="Admitido",
            par_eve_qr="pdf/qr_participante/qr1.png",
            par_eve_clave="clave123",
            par_eve_calificacion_final=4.5,
            par_eve_proyecto=self.proyecto,
            habilitado=True
        )

        # --- Crear Evaluador ---
        self.usuario_eval = Usuario.objects.create_user(
            username="eval01",
            password="evalpass",
            first_name="Carlos",
            last_name="Gómez",
            documento_identidad="112233"
        )
        self.evaluador = Evaluadores.objects.create(usuario=self.usuario_eval)

        # --- Crear Criterio ---
        self.criterio = Criterios.objects.create(
            cri_descripcion="Originalidad e Innovación",
            cri_peso=40.0,
            cri_evento_fk=self.evento
        )

        # --- Crear Calificación ---
        self.calificacion = Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio,
            clas_proyecto_fk=self.proyecto,
            cal_valor=4.5,
            cal_comentario="Excelente presentación e innovación."
        )

        # --- URL de la vista ---
        self.url = reverse('app_participante:descargar_comentarios', args=[self.evento.id])

    def test_pdf_generado_correctamente(self):
        """✅ El PDF se genera correctamente con contenido válido"""
        self.client.force_login(self.usuario_participante)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF', response.content[:10])

    def test_pdf_sin_calificaciones_no_falla(self):
        """⚠️ El PDF se genera aunque no existan calificaciones"""
        Calificaciones.objects.all().delete()
        self.client.force_login(self.usuario_participante)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'%PDF', response.content[:10])
