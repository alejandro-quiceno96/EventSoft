import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from app_eventos.models import Eventos, EvaluadoresEventos
from app_evaluador.models import Evaluadores
from app_administrador.models import Administradores
from app_usuarios.models import Usuario

@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media/'))
class CancelarInscripcionEvaluadorTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='evaluador_cancelar',
            password='12345',
            tipo_documento='CC',
            documento_identidad='5555555'
        )
        self.client.login(username='evaluador_cancelar', password='12345')

        self.admin = Administradores.objects.create(usuario=self.user)
        self.evento = Eventos.objects.create(
            eve_nombre='Evento de Prueba',
            eve_descripcion='Evento para probar cancelación',
            eve_ciudad='Manizales',
            eve_lugar='Centro de Eventos',
            eve_fecha_inicio='2025-11-20',
            eve_fecha_fin='2025-11-22',
            eve_estado='Activo',
            eve_imagen='image/test.png',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        # Crear evaluador y preinscripción
        self.evaluador = Evaluadores.objects.create(usuario=self.user)
        self.archivo = SimpleUploadedFile("cv.pdf", b"contenido", content_type="application/pdf")

        self.inscripcion = EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador,
            eva_eve_evento_fk=self.evento,
            eva_eve_areas_interes='IA',
            eva_eve_fecha_hora=timezone.now(),
            eva_eve_documentos=self.archivo,
            eva_estado='Pendiente'
        )

        self.url = reverse('app_evaluador:cancelar_inscripcion', args=[self.evento.id, self.evaluador.id])

    def tearDown(self):
        """Limpia archivos creados en pruebas"""
        media_path = os.path.join(settings.BASE_DIR, 'test_media/')
        if os.path.exists(media_path):
            for root, dirs, files in os.walk(media_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))

    def test_cancelacion_exitosa(self):
        """CA1: El evaluador puede cancelar su preinscripción exitosamente"""
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('app_evaluador:principal_evaluador'))
        self.assertFalse(EvaluadoresEventos.objects.filter(id=self.inscripcion.id).exists())

    def test_eliminar_evaluador_sin_mas_inscripciones(self):
        """CA2: El evaluador se elimina si no tiene más inscripciones"""
        self.client.post(self.url)
        self.assertFalse(Evaluadores.objects.filter(id=self.evaluador.id).exists())

    def test_metodo_no_permitido(self):
        """CA3: Si la solicitud no es POST, redirige sin eliminar"""
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('app_evaluador:principal_evaluador'))
        self.assertTrue(EvaluadoresEventos.objects.filter(id=self.inscripcion.id).exists())

    def test_no_elimina_archivo_inexistente(self):
        """Verifica que no falle si el documento no existe físicamente"""
        # Elimina manualmente el archivo del sistema
        if os.path.exists(self.inscripcion.eva_eve_documentos.path):
            os.remove(self.inscripcion.eva_eve_documentos.path)

        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('app_evaluador:principal_evaluador'))
        self.assertFalse(EvaluadoresEventos.objects.filter(id=self.inscripcion.id).exists())
