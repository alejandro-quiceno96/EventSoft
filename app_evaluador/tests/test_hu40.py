from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_eventos.models import Eventos, Proyecto, ParticipantesEventos, EvaluadoresEventos
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores, EvaluadorProyecto


class ListadoParticipantesEvaluadorTestCase(TestCase):
    """
    Historia de Usuario HU-40:
    Como evaluador, quiero visualizar el listado de los participantes
    del evento en el que soy evaluador, para saber cuántos y quiénes van a participar.
    """

    def setUp(self):
        # Cliente
        self.client = Client()

        # ----- ADMINISTRADOR -----
        self.user_admin = Usuario.objects.create_user(
            username='admin', password='admin123', first_name='Admin', last_name='Principal'
        )
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # ----- EVALUADOR -----
        self.user_eval = Usuario.objects.create_user(
            username='evaluador', password='12345', first_name='Carlos', last_name='Gómez'
        )
        self.evaluador = Evaluadores.objects.create(usuario=self.user_eval)

        # ----- EVENTO -----
        self.evento = Eventos.objects.create(
            eve_nombre='Congreso Innovación 2025',
            eve_descripcion='Evento sobre proyectos tecnológicos',
            eve_ciudad='Manizales',
            eve_lugar='Recinto del Pensamiento',
            eve_fecha_inicio='2025-11-10',
            eve_fecha_fin='2025-11-12',
            eve_estado='Activo',
            eve_imagen='image/evento.jpg',
            eve_capacidad=150,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # ----- PARTICIPANTE -----
        self.user_part = Usuario.objects.create_user(
            username='juanperez',
            password='12345',
            first_name='Juan',
            last_name='Pérez'
        )
        self.participante = Participantes.objects.create(usuario=self.user_part)

        # ----- PROYECTO -----
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo='PROJ001',
            pro_nombre='Energía Solar Inteligente',
            pro_descripcion='Sistema de paneles solares inteligentes.',
            pro_documentos=SimpleUploadedFile("proyecto.pdf", b"contenido pdf"),
            pro_estado='Activo'
        )

        # ----- RELACIÓN PARTICIPANTE-EVENTO -----
        self.participante_evento = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos='pdf/proyectos/solar.pdf',
            par_eve_estado='Inscrito',
            par_eve_qr='pdf/qr_participante/qr.png',
            par_eve_clave='12345',
            par_eve_proyecto=self.proyecto
        )

        # ----- RELACIÓN EVALUADOR-PROYECTO -----
        self.evaluador_proyecto = EvaluadorProyecto.objects.create(
            eva_pro_evaluador_fk=self.evaluador,
            eva_pro_proyecto_fk=self.proyecto
        )

        # ----- URL DETALLE EVENTO -----
        self.url = reverse('app_evaluador:detalle_evento_evaluador', args=[self.evaluador.id, self.evento.id])

    # -------------------------------------------------------------------
    # ✅ Criterios de Aceptación
    # -------------------------------------------------------------------

    def test_visualizacion_listado_participantes(self):
        """CA1: El evaluador visualiza correctamente la lista de participantes (expositores en modal)"""
        self.client.login(username='evaluador', password='12345')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_evaluador/detalle_evento.html')

        proyectos = response.context['proyectos']
        self.assertTrue(len(proyectos) > 0, "No se encontró ningún proyecto en el contexto")

        nombres_expositores = proyectos[0]['expositores']
        self.assertIn('Juan Pérez', nombres_expositores)

    def test_participantes_relacionados_evento(self):
        """CA2: Los participantes listados pertenecen al evento del evaluador"""
        self.client.login(username='evaluador', password='12345')
        response = self.client.get(self.url)

        proyectos = response.context['proyectos']
        for p in proyectos:
            expositores = p['expositores']
            self.assertGreater(len(expositores), 0)
            self.assertIn('Juan Pérez', expositores)

    def test_proyectos_relacionados_con_evaluador(self):
        """CA3: Solo se muestran proyectos asignados al evaluador"""
        self.client.login(username='evaluador', password='12345')
        response = self.client.get(self.url)

        proyectos = response.context['proyectos']
        nombres_proyectos = [p['pro_nombre'] for p in proyectos]
        self.assertIn('Energía Solar Inteligente', nombres_proyectos)
