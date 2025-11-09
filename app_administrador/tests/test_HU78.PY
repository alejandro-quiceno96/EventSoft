from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from app_eventos.models import Eventos, Proyecto
from app_criterios.models import Criterios
from app_evaluador.models import Evaluadores, Calificaciones
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User

class DetallesCalificacionesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear administrador
        self.user_admin = User.objects.create_user(username="admin1", password="1234")
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Test",
            eve_descripcion="Descripcion",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear proyecto
        self.proyecto = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PRJ001",
            pro_nombre="Proyecto Test",
            pro_descripcion="Desc",
            pro_documentos="doc.pdf",
            pro_estado="Aceptado"
        )

        # Crear criterios
        self.criterio1 = Criterios.objects.create(cri_descripcion="Originalidad", cri_peso=50, cri_evento_fk=self.evento)
        self.criterio2 = Criterios.objects.create(cri_descripcion="Impacto", cri_peso=50, cri_evento_fk=self.evento)

        # Crear evaluadores
        self.user_eval1 = User.objects.create_user(username="eval1", password="1234")
        self.user_eval2 = User.objects.create_user(username="eval2", password="1234")

        self.evaluador1 = Evaluadores.objects.create(usuario=self.user_eval1)
        self.evaluador2 = Evaluadores.objects.create(usuario=self.user_eval2)

        # Crear calificaciones
        Calificaciones.objects.create(cal_evaluador_fk=self.evaluador1, cal_criterio_fk=self.criterio1, clas_proyecto_fk=self.proyecto, cal_valor=80)
        Calificaciones.objects.create(cal_evaluador_fk=self.evaluador1, cal_criterio_fk=self.criterio2, clas_proyecto_fk=self.proyecto, cal_valor=90)
        Calificaciones.objects.create(cal_evaluador_fk=self.evaluador2, cal_criterio_fk=self.criterio1, clas_proyecto_fk=self.proyecto, cal_valor=70)

        self.client.login(username="admin1", password="1234")

    def test_detalles_calificaciones_multiples_evaluadores(self):
        url = reverse('administrador:detalle_calificaciones', args=[self.evento.id, self.proyecto.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.context['evaluadores_data']
        self.assertEqual(len(list(data)), 2)  # dos evaluadores
        # Verificar puntaje total ponderado
        for d in data:
            if d['evaluador'].id == self.evaluador1.id:
                self.assertAlmostEqual(d['puntaje_total'], 85)  # (80*0.5 + 90*0.5)
            if d['evaluador'].id == self.evaluador2.id:
                self.assertAlmostEqual(d['puntaje_total'], 35)  # (70*0.5)

    def test_detalle_calificacion_individual(self):
        url = reverse('administrador:detalle_calificacion', args=[self.proyecto.id, self.evaluador1.id, self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        info = response.context['calificaciones_info']
        self.assertEqual(len(info), 2)  # 2 criterios
        self.assertAlmostEqual(response.context['puntaje_total'], 85)

    def test_proyecto_sin_calificaciones(self):
        proyecto2 = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PRJ002",
            pro_nombre="Proyecto vacío",
            pro_descripcion="Desc",
            pro_documentos="doc.pdf",
            pro_estado="Aceptado"
        )
        url = reverse('administrador:detalle_calificaciones', args=[self.evento.id, proyecto2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(response.context['evaluadores_data'])), 0)

    def test_evento_inexistente(self):
        url = reverse('administrador:detalle_calificaciones', args=[999, self.proyecto.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_proyecto_inexistente(self):
        url = reverse('administrador:detalle_calificacion', args=[999, self.evaluador1.id, self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
