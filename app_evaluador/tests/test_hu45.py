from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from app_eventos.models import Eventos, ParticipantesEventos, Proyecto
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores, Calificaciones
from app_criterios.models import Criterios
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User


class EvaluarParticipanteTestCase(TestCase):
    """HUXX: Calificar el desempeño de un participante utilizando el instrumento de evaluación del evento"""

    def setUp(self):
        # --- Cliente autenticado ---
        self.client = Client()

        # --- Crear usuario administrador ---
        self.admin_user = User.objects.create_user(username="admin", password="12345")
        self.admin = Administradores.objects.create(usuario=self.admin_user)

        # --- Crear evaluador ---
        self.user_evaluador = User.objects.create_user(username="evaluador1", password="12345")
        self.evaluador = Evaluadores.objects.create(usuario=self.user_evaluador)

        # --- Crear participante ---
        self.user_participante = User.objects.create_user(username="juan", password="12345")
        self.participante = Participantes.objects.create(usuario=self.user_participante)

        # --- Crear evento ---
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Ciencia 2025",
            eve_descripcion="Evento de ciencia juvenil",
            eve_ciudad="Manizales",
            eve_lugar="Recinto del Pensamiento",
            eve_fecha_inicio=timezone.now().date(),
            eve_fecha_fin=timezone.now().date(),
            eve_estado="Activo",
            eve_imagen="image/test.png",
            eve_capacidad=100,
            eve_administrador_fk=self.admin,
        )

        # --- Crear proyecto ---
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="P001",
            pro_nombre="Proyecto Solar",
            pro_descripcion="Panel solar portátil",
            pro_documentos="pdf/proyecto.pdf",
            pro_estado="Activo",
        )

        # --- Relación participante-evento ---
        self.part_evento = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_estado="Aprobado",
            par_eve_qr="pdf/qr/1.pdf",
            par_eve_clave="clave123",
            par_eve_proyecto=self.proyecto,
        )

        # --- Crear criterios de evaluación ---
        self.criterio1 = Criterios.objects.create(
            cri_descripcion="Innovación",
            cri_peso=Decimal('50.0'),
            cri_evento_fk=self.evento
        )
        self.criterio2 = Criterios.objects.create(
            cri_descripcion="Presentación",
            cri_peso=Decimal('50.0'),
            cri_evento_fk=self.evento
        )

        # --- Login evaluador ---
        self.client.login(username="evaluador1", password="12345")

        # --- URL de evaluación ---
        self.url = reverse('app_evaluador:evaluar_participante', kwargs={
            'evento_id': self.evento.id,
            'proyecto_id': self.proyecto.id,
            'evaluador_id': self.evaluador.id
        })

    def test_acceso_vista_evaluacion(self):
        """CA1: El evaluador accede correctamente al formulario de evaluación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_evaluador/evaluar_participante.html')
        self.assertContains(response, "Proyecto Solar")
        self.assertContains(response, "Innovación")
        self.assertContains(response, "Presentación")

    def test_registro_calificaciones_y_promedio(self):
        """CA2: El evaluador registra calificaciones y el sistema calcula el promedio ponderado correctamente"""
        data = {
            f'puntaje_{self.criterio1.id}': '80',
            f'comentario_{self.criterio1.id}': 'Buena innovación',
            f'puntaje_{self.criterio2.id}': '100',
            f'comentario_{self.criterio2.id}': 'Excelente presentación',
        }

        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verificar que se crearon las calificaciones
        calificaciones = Calificaciones.objects.filter(clas_proyecto_fk=self.proyecto)
        self.assertEqual(calificaciones.count(), 2)

        # Calcular promedio esperado (80*0.5 + 100*0.5 = 90)
        self.proyecto.refresh_from_db()
        self.assertEqual(float(self.proyecto.pro_calificación_final), 90.0)

        # Verificar que el participante también tenga la calificación
        self.part_evento.refresh_from_db()
        self.assertEqual(float(self.part_evento.par_eve_calificacion_final), 90.0)

        # Mensaje de éxito
        messages = list(response.context['messages'])
        self.assertTrue(any("Evaluación guardada correctamente" in str(m) for m in messages))
