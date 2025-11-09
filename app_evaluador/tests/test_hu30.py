import io
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.utils import timezone

from app_evaluador.models import Evaluadores
from app_eventos.models import Eventos, EvaluadoresEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario

class RegistrarEvaluadorTestCase(TestCase):
    def setUp(self):
        # Cliente y usuario autenticado
        self.client = Client()
        self.user = Usuario.objects.create_user(
            username='evaluador1',
            password='12345',
            tipo_documento='CC',
            documento_identidad='100100100'
        )
        self.client.login(username='evaluador1', password='12345')

        # Crear administrador y evento
        self.admin = Administradores.objects.create(usuario=self.user)
        self.evento = Eventos.objects.create(
            eve_nombre='Congreso de Tecnología',
            eve_descripcion='Evento sobre innovación',
            eve_ciudad='Manizales',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio='2025-12-01',
            eve_fecha_fin='2025-12-03',
            eve_estado='Activo',
            eve_imagen='image/test.png',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        self.url = reverse('registrar_evaluador', args=[self.evento.id])
        self.file = SimpleUploadedFile("cv.pdf", b"PDF content", content_type="application/pdf")

    def test_registro_exitoso_evaluador(self):
        """CA1: El evaluador puede registrarse correctamente si no está inscrito"""
        response = self.client.post(self.url, {
            'area': 'Ciencias de Datos',
            'documento': self.file
        })

        self.assertRedirects(response, reverse('inicio_visitante') + '?registro=exito_evaluador')
        self.assertTrue(EvaluadoresEventos.objects.filter(eva_eve_evento_fk=self.evento).exists())

    def test_prevenir_registro_duplicado(self):
        """CA2: No debe permitir inscripción duplicada"""
        evaluador = Evaluadores.objects.create(usuario=self.user)
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=evaluador,
            eva_eve_evento_fk=self.evento,
            eva_eve_areas_interes='AI',
            eva_eve_fecha_hora=timezone.now(),
            eva_estado='Pendiente'
        )

        response = self.client.post(self.url, {
            'area': 'AI',
            'documento': self.file
        })

        self.assertRedirects(response, reverse('inicio_visitante') + '?error=ya_inscrito_evaluador')

    def test_evento_no_existe(self):
        """CA3: Si el evento no existe, redirige con error"""
        url_invalida = reverse('registrar_evaluador', args=[999])
        response = self.client.post(url_invalida, {
            'area': 'IA',
            'documento': self.file
        })

        self.assertRedirects(response, reverse('inicio_visitante') + '?error=evento_no_existe')
