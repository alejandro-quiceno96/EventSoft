from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.utils import timezone
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, ParticipantesEventos
from app_administrador.models import Administradores
from app_participante.models import Participantes
import datetime
import json

class CancelarInscripcionParticipanteTest(TestCase):
    def setUp(self):
        self.client = Client()

        # ✔️ Usuario participante: usa create_user para que la password quede hasheada
        self.usuario_participante = Usuario.objects.create_user(
            username="participante_datos",
            email="participante_datos@test.com",
            password="test12345",
            tipo_documento="CC",
            documento_identidad="3333",
            telefono="3010000001"
        )

        # ✔️ Instancia Participantes relacionada al Usuario (asumo que Participantes tiene FK a Usuario llamada 'usuario')
        self.participante = Participantes.objects.create(
            usuario=self.usuario_participante,
            # agrega aquí otros campos requeridos por tu modelo Participantes si los tienes
        )

        # ✔️ Usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )

        # ✔️ Administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # ✔️ Evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test',
            eve_descripcion='Desc test',
            eve_ciudad='Caldas',
            eve_lugar='Manizales',
            eve_fecha_inicio=datetime.date(2025, 10, 10),
            eve_fecha_fin=datetime.date(2025, 10, 12),
            eve_estado='Activo',
            eve_imagen='image/test.jpg',
            eve_capacidad=100,
            eve_administrador_fk=self.admin,
        )

        # ✔️ Archivo de prueba
        archivo = SimpleUploadedFile("documento.pdf", b"contenido de prueba", content_type="application/pdf")

        # ✔️ Inscripción del participante al evento
        self.inscripcion = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,  # Participantes (no Usuario)
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión",
            par_eve_documentos=archivo,
            par_eve_fecha_hora=timezone.now()
        )

        # ✔️ URL de la vista a probar
        # Asumo que la URL está nombrada 'app_participante:cancelar_inscripcion'
        # y recibe (evento_id, participante_id) en ese orden.
        self.url = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, self.participante.id])

    def test_login_required_redirects(self):
        """Debe redirigir al login si el usuario no ha iniciado sesión"""
        response = self.client.post(self.url)
        # Django por defecto hace redirect 302 a settings.LOGIN_URL cuando usa @login_required
        self.assertEqual(response.status_code, 302)
        # El Location suele contener settings.LOGIN_URL (puede variar según configuración)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_cancelar_inscripcion_exitosa(self):
        """Debe cancelar correctamente la inscripción existente y devolver JSON success"""
        # Hacemos login con el usuario participante creado
        logged = self.client.login(username='participante_datos', password='test12345')
        self.assertTrue(logged, "Falló el login del participante de prueba")

        response = self.client.post(self.url)
        # Asumo que la vista devuelve JsonResponse({'success': True}, status=200)
        self.assertEqual(response.status_code, 200)
        # Comprobamos JSON (puede ajustarse si devuelves otra estructura)
        content = json.loads(response.content.decode())
        self.assertEqual(content, {"success": True})

        # Verificar que la inscripción fue eliminada (o que su estado cambió, según la lógica real)
        self.assertFalse(ParticipantesEventos.objects.filter(id=self.inscripcion.id).exists())

    def test_cancelar_inscripcion_no_existente(self):
        """Debe devolver 404 si la inscripción asociada no existe"""
        logged = self.client.login(username='participante_datos', password='test12345')
        self.assertTrue(logged)

        # Usamos un event_id inexistente (o inscrpción inexistente)
        bad_url = reverse('app_participante:cancelar_inscripcion', args=[9999, self.participante.id])
        response = self.client.post(bad_url)
        # Asumo que tu vista lanza Http404 o devuelve HttpResponseNotFound
        self.assertEqual(response.status_code, 404)

    def test_metodo_no_permitido(self):
        """Debe devolver 405 si se accede por GET (si la vista solo permite POST)"""
        logged = self.client.login(username='participante_datos', password='test12345')
        self.assertTrue(logged)

        response = self.client.get(self.url)
        # Si usas @require_POST de Django, devuelve 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        # opcional: comprobar que la respuesta menciona 'Method Not Allowed'
        self.assertIn('Method', response.content.decode() or '')
