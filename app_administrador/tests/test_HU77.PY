from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from decimal import Decimal
from app_eventos.models import Eventos, Proyecto
from app_criterios.models import Criterios
from app_evaluador.models import Evaluadores
from app_participante.models import Participantes
from app_evaluador.models import Calificaciones
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User

class TablaCalificacionesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear administrador
        self.user_admin = User.objects.create_user(username="admin1", password="1234")
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Criterios",
            eve_descripcion="Prueba HU74",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="img.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear proyecto
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PRJ001",
            pro_nombre="Proyecto Test",
            pro_descripcion="Descripcion proyecto",
            pro_documentos="doc.pdf",
            pro_estado="Aceptado",
        )

        # Crear criterios
        self.criterio1 = Criterios.objects.create(
            cri_descripcion="Originalidad",
            cri_peso=50,
            cri_evento_fk=self.evento
        )
        self.criterio2 = Criterios.objects.create(
            cri_descripcion="Impacto",
            cri_peso=50,
            cri_evento_fk=self.evento
        )

        # Crear evaluador y calificaciones
        self.evaluador = Evaluadores.objects.create(usuario=self.user_admin)
        Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio1,
            clas_proyecto_fk=self.proyecto,
            cal_valor=80
        )
        Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio2,
            clas_proyecto_fk=self.proyecto,
            cal_valor=90
        )

        # Login admin
        self.client.login(username="admin1", password="1234")

    def test_ranking_con_calificaciones(self):
        url = reverse('administrador:tabla_calificaciones', args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        ranking = response.context['ranking']
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]['proyecto'], "Proyecto Test")
        # Puntaje ponderado: (80*50/100 + 90*50/100) = 85
        self.assertAlmostEqual(ranking[0]['puntaje_final'], 85)


    def test_evento_sin_proyectos(self):
        evento2 = Eventos.objects.create(
            eve_nombre="Evento Vacío",
            eve_descripcion="Desc",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        url = reverse('administrador:tabla_calificaciones', args=[evento2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ranking'], [])

    def test_descargar_ranking_pdf(self):
        url = reverse('administrador:descargar_ranking_pdf', args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="ranking_evento_{self.evento.id}.pdf"')
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_evento_inexistente(self):
        url = reverse('administrador:tabla_calificaciones', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
