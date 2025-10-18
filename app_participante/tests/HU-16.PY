from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase, Client
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, ParticipantesEventos
from app_administrador.models import Administradores
from app_participante.models import Participantes
import datetime
from django.utils import timezone

class CancelarInscripcionParticipanteTest(TestCase):
    def setUp(self):
        self.client = Client()

        
        

        # 🔹 Participante asociado (objeto relacionado)
        self.participante = Usuario.objects.create(
            username="participante_datos",
            email="participante_datos@test.com",
            password="test12345",
            tipo_documento="CC",
            documento_identidad="3333",
            telefono="3010000001"
        )
        self.participante = Participantes.objects.create(
        usuario=self.participante,
    # cualquier otro campo que requiera Participantes
)


        # 🔹 Usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )

        # 🔹 Administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # 🔹 Evento de prueba
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

        # 🔹 Archivo de prueba
        archivo = SimpleUploadedFile("documento.pdf", b"contenido de prueba", content_type="application/pdf")

        # 🔹 Inscripción del participante al evento
        self.inscripcion = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,  # ✅ Ahora sí es un Participante
            par_eve_evento_fk=self.evento,
            par_eve_estado="Pendiente de Revisión",
            par_eve_documentos=archivo,
            par_eve_fecha_hora=timezone.now()
        )

        # 🔹 URL de la vista a probar
        self.url = self.url = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, self.participante.id])


    def test_login_required_redirects(self):
        """Debe redirigir al login si el usuario no ha iniciado sesión"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_cancelar_inscripcion_exitosa(self):
        """Debe cancelar correctamente la inscripción existente"""
        self.client.login(username='app_paticipante:participante_cancelar', password='test12345')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

        # Verificar que la inscripción fue eliminada
        self.assertFalse(ParticipantesEventos.objects.filter(id=self.inscripcion.id).exists())

    def test_cancelar_inscripcion_no_existente(self):
        """Debe devolver error si la inscripción no existe"""
        self.client.login(username='app_participante:participante_cancelar', password='test12345')

        # Usamos un evento inexistente
        bad_url = reverse('app_visitante:cancelar_inscripcion', args=[9999, self.participante.id])
        response = self.client.post(bad_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No se encontró la inscripción", str(response.content))

    def test_metodo_no_permitido(self):
        """Debe devolver error si se accede por GET"""
        self.client.login(username='participante_cancelar', password='test12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Método no permitido", str(response.content))
