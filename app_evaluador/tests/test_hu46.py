from django.test import TestCase, Client
from django.urls import reverse
from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_evaluador.models import Evaluadores, EvaluadorProyecto, Calificaciones
from app_participante.models import Participantes
from datetime import date, datetime
from app_usuarios.models import Usuario as User
from app_administrador.models import Administradores


class VerParticipantesRankingTestCase(TestCase):
    def setUp(self):
        # Crear usuario y evaluador
        self.user = User.objects.create_user(username='evaluador1', password='12345')
        self.evaluador = Evaluadores.objects.create(usuario=self.user)

        # Crear usuario administrador y su instancia
        self.admin_user = User.objects.create_user(username='admin1', password='adminpass')
        self.administrador = Administradores.objects.create(usuario=self.admin_user)

        # Crear evento con administrador válido
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Ciencia 2025",
            eve_descripcion="Evento de proyectos científicos",
            eve_ciudad="Manizales",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today(),
            eve_estado="Activo",
            eve_imagen="image/test.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,  # ✅ aquí la corrección
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        # Crear proyectos
        self.proyecto1 = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PR001",
            pro_nombre="Energía Solar",
            pro_descripcion="Proyecto sobre paneles solares",
            pro_documentos="pdf/proyectos/solar.pdf",
            pro_estado="Aprobado",
            pro_calificación_final=95.5
        )

        self.proyecto2 = Proyecto.objects.create(
            pro_evento_fk=self.evento,
            pro_codigo="PR002",
            pro_nombre="Robótica Educativa",
            pro_descripcion="Proyecto sobre robótica para niños",
            pro_documentos="pdf/proyectos/robot.pdf",
            pro_estado="Aprobado",
            pro_calificación_final=88.0
        )

        # Asociar evaluador a proyectos
        EvaluadorProyecto.objects.create(
            eva_pro_evaluador_fk=self.evaluador,
            eva_pro_proyecto_fk=self.proyecto1
        )

        EvaluadorProyecto.objects.create(
            eva_pro_evaluador_fk=self.evaluador,
            eva_pro_proyecto_fk=self.proyecto2
        )

        # Crear participante y su relación con evento/proyecto
        self.participante_user = User.objects.create_user(username='participante1', password='abc123')
        self.participante = Participantes.objects.create(usuario=self.participante_user)
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=datetime.now(),
            par_eve_documentos="pdf/proyectos/doc.pdf",
            par_eve_estado="Aprobado",
            par_eve_qr="pdf/qr_participante/qr.pdf",
            par_eve_clave="clave1",
            par_eve_proyecto=self.proyecto1
        )

        self.client = Client()

    def test_ranking_visible_para_evaluador(self):
        """Verifica que el evaluador autenticado pueda acceder a la vista y vea el ranking"""
        self.client.login(username='evaluador1', password='12345')
        url = reverse('app_evaluador:ver_participantes', args=[self.evento.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('ranking', response.context)
        ranking = response.context['ranking']

        # Debe estar ordenado de mayor a menor
        self.assertGreaterEqual(ranking[0]['pro_calificacion_final'], ranking[1]['pro_calificacion_final'])

    def test_datos_completos_en_ranking(self):
        """Verifica que cada proyecto en el ranking tenga los datos necesarios"""
        self.client.login(username='evaluador1', password='12345')
        url = reverse('app_evaluador:ver_participantes', args=[self.evento.id])
        response = self.client.get(url)
        ranking = response.context['ranking']

        for proyecto in ranking:
            self.assertIn('pro_nombre', proyecto)
            self.assertIn('pro_codigo', proyecto)
            self.assertIn('pro_calificacion_final', proyecto)
            self.assertIn('expositores', proyecto)

    def test_filtrado_por_evento_y_evaluador(self):
        """Verifica que solo se muestren proyectos del evento y evaluador autenticado"""
        # Crear otro evento con el mismo administrador existente
        otro_evento = Eventos.objects.create(
            eve_nombre="Evento Tech",
            eve_descripcion="Otro evento",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today(),
            eve_estado="Activo",
            eve_imagen="image/test2.jpg",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador,  # ✅ Corrección clave
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        Proyecto.objects.create(
            pro_evento_fk=otro_evento,
            pro_codigo="PR999",
            pro_nombre="Otro Proyecto",
            pro_descripcion="No debe mostrarse",
            pro_documentos="pdf/proyectos/otro.pdf",
            pro_estado="Aprobado",
            pro_calificación_final=99.0
        )

        self.client.login(username='evaluador1', password='12345')
        url = reverse('app_evaluador:ver_participantes', args=[self.evento.id])
        response = self.client.get(url)
        ranking = response.context['ranking']

        # Verificamos que el proyecto del otro evento no aparezca
        nombres_proyectos = [p['pro_nombre'] for p in ranking]
        self.assertNotIn("Otro Proyecto", nombres_proyectos)

