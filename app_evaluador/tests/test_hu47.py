from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from app_eventos.models import Eventos, Proyecto
from app_evaluador.models import Evaluadores, Calificaciones
from app_criterios.models import Criterios
from app_administrador.models import Administradores
from datetime import date
from app_usuarios.models import Usuario as User


class ApiCalificacionesTestCase(TestCase):
    def setUp(self):
        # Crear usuarios
        self.user_eval = User.objects.create_user(username='evaluador1', password='12345')
        self.user_admin = User.objects.create_user(username='admin1', password='adminpass')

        # Crear roles
        self.admin = Administradores.objects.create(usuario=self.user_admin)
        self.evaluador = Evaluadores.objects.create(usuario=self.user_eval)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Innovación 2025",
            eve_descripcion="Evaluación de proyectos innovadores",
            eve_ciudad="Medellín",
            eve_lugar="Plaza Mayor",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today(),
            eve_estado="Activo",
            eve_imagen="image/test.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        # Crear proyecto
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PJT001",
            pro_nombre="Robot Educativo",
            pro_descripcion="Proyecto de robótica para educación",
            pro_documentos="pdf/proyectos/robot.pdf",
            pro_estado="Aprobado",
            pro_calificación_final=90.0
        )

        # Crear criterios
        self.criterio1 = Criterios.objects.create(
            cri_descripcion="Creatividad",
            cri_peso=0.3,
            cri_evento_fk=self.evento
        )

        self.criterio2 = Criterios.objects.create(
            cri_descripcion="Impacto Social",
            cri_peso=0.7,
            cri_evento_fk=self.evento
        )

        # Crear calificaciones del evaluador
        Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio1,
            clas_proyecto_fk=self.proyecto,
            cal_valor=85.0,
            cal_comentario="Buena creatividad"
        )

        Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio2,
            clas_proyecto_fk=self.proyecto,
            cal_valor=95.0,
            cal_comentario="Excelente impacto"
        )

        self.client = Client()

    def test_api_retorna_json_con_calificaciones(self):
        """Verifica que la API retorne un JSON con las calificaciones del evaluador"""
        url = reverse('app_evaluador:api_calificaciones', args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)

        data = response.json()
        self.assertIn('calificaciones', data)
        self.assertEqual(len(data['calificaciones']), 2)

    def test_campos_correctos_en_respuesta(self):
        """Verifica que cada calificación tenga los campos requeridos"""
        url = reverse('app_evaluador:api_calificaciones', args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        response = self.client.get(url)
        data = response.json()['calificaciones']

        for cal in data:
            self.assertIn('criterio', cal)
            self.assertIn('peso', cal)
            self.assertIn('puntaje', cal)
            self.assertIn('comentario', cal)

    def test_no_retorna_calificaciones_de_otro_evaluador(self):
        """Verifica que las calificaciones sean solo del evaluador autenticado"""
        # Crear otro evaluador y calificación
        otro_user = User.objects.create_user(username='evaluador2', password='abc123')
        otro_eval = Evaluadores.objects.create(usuario=otro_user)

        Calificaciones.objects.create(
            cal_evaluador_fk=otro_eval,
            cal_criterio_fk=self.criterio1,
            clas_proyecto_fk=self.proyecto,
            cal_valor=50.0,
            cal_comentario="No debe mostrarse"
        )

        url = reverse('app_evaluador:api_calificaciones', args=[self.evento.id, self.proyecto.id, self.evaluador.id])
        response = self.client.get(url)
        data = response.json()['calificaciones']

        criterios_devueltos = [c['criterio'] for c in data]
        self.assertNotIn("No debe mostrarse", criterios_devueltos)
        self.assertEqual(len(data), 2)
