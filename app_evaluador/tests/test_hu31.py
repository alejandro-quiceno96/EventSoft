import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from app_evaluador.models import Evaluadores
from app_eventos.models import Eventos, EvaluadoresEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario

@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media/'))
class ModificarPreinscripcionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='evaluador_mod',
            password='12345',
            tipo_documento='CC',
            documento_identidad='123456789'
        )
        self.client.login(username='evaluador_mod', password='12345')

        self.admin = Administradores.objects.create(usuario=self.user)
        self.evento = Eventos.objects.create(
            eve_nombre='Congreso Innovación',
            eve_descripcion='Evento de innovación',
            eve_ciudad='Manizales',
            eve_lugar='Teatro Fundadores',
            eve_fecha_inicio='2025-11-10',
            eve_fecha_fin='2025-11-12',
            eve_estado='Activo',
            eve_imagen='image/test.png',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        self.evaluador = Evaluadores.objects.create(usuario=self.user)

        # Documento inicial
        self.archivo_inicial = SimpleUploadedFile("cv_v1.pdf", b"version1", content_type="application/pdf")

        self.registro = EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=self.evaluador,
            eva_eve_evento_fk=self.evento,
            eva_eve_areas_interes='Ciencia de Datos',
            eva_eve_fecha_hora=timezone.now(),
            eva_eve_documentos=self.archivo_inicial,
            eva_estado='Pendiente'
        )

        self.url = reverse('app_evaluador:modificar_preinscripcion', args=[self.evento.id, self.evaluador.id])

    def tearDown(self):
        """Elimina los archivos creados durante las pruebas"""
        media_path = os.path.join(settings.BASE_DIR, 'test_media/')
        if os.path.exists(media_path):
            for root, dirs, files in os.walk(media_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))

    def test_actualizacion_exitosa_documento(self):
        """CA1: El evaluador puede reemplazar su documento"""
        nuevo_doc = SimpleUploadedFile("cv_v2.pdf", b"version2", content_type="application/pdf")

        response = self.client.post(self.url, {'documento': nuevo_doc})

        self.assertRedirects(response, reverse('app_evaluador:principal_evaluador'))
        evaluador_actualizado = EvaluadoresEventos.objects.get(id=self.registro.id)
        self.assertTrue('cv_v2.pdf' in str(evaluador_actualizado.eva_eve_documentos))

    def test_evaluador_no_encontrado(self):
        """CA2: Retorna 404 si el evaluador/evento no existen"""
        url_invalida = reverse('app_evaluador:modificar_preinscripcion', args=[999, 999])
        response = self.client.post(url_invalida)
        self.assertEqual(response.status_code, 404)

    def test_metodo_no_permitido(self):
        """CA3: Retorna error 405 si se usa GET"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertJSONEqual(response.content, {'error': 'Método no permitido'})
