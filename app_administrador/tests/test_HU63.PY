# app_administrador/tests/test_hu63.py

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now

from app_eventos.models import Eventos, Proyecto, ParticipantesEventos
from app_participante.models import Participantes
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User

class VerProyectosAceptadosTestCase(TestCase):
    """
    HU63 - ADMINISTRADOR EVENTO:
    Ver los datos de los participantes aceptados en un evento y la documentación aportada.
    """

    def setUp(self):
        """Configura los datos iniciales para las pruebas"""
        self.client = Client()

        # Crear usuario administrador del sistema
        self.user_admin = User.objects.create_user(
            username="admin1",
            password="admin123",
            first_name="Carlos",
            last_name="López",
            is_staff=True
        )

        # Crear objeto Administrador relacionado con el usuario
        self.admin = Administradores.objects.create(
            usuario=self.user_admin
        )

        # Crear evento principal
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Ciencia 2025",
            eve_descripcion="Evento de innovación científica",
            eve_ciudad="Manizales",
            eve_lugar="Centro Cultural",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="image/evento.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear participante
        self.participante = Participantes.objects.create(
            usuario=User.objects.create_user(
                username="part1",
                password="1234",
                first_name="Laura",
                last_name="Gómez"
            )
        )

        # Crear proyecto aceptado
        self.proyecto = Proyecto.objects.create(
            pro_codigo="PRJ001",
            pro_nombre="Energía Verde",
            pro_descripcion="Proyecto sobre energía solar",
            pro_documentos="documento.pdf",
            pro_estado="Aceptado",
            pro_fecha_hora=now(),
            pro_calificación_final=95,
            pro_evento_fk=self.evento
        )

        # Vincular participante con el proyecto en el evento
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento,
            par_eve_proyecto=self.proyecto,
            par_eve_fecha_hora=now(),
            par_eve_estado="Aceptado",
            par_eve_documentos="documento.pdf",
            par_eve_qr="qr.pdf",
            par_eve_clave="12345",
            habilitado=True
        )

    # ---------------------- TESTS ----------------------

    def test_acceso_autenticado(self):
        """CA1: Verifica que el administrador autenticado pueda acceder a la vista"""
        self.client.login(username="admin1", password="admin123")

        url = reverse("administrador:ver_participantes", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_administrador/ver_participantes.html")

    def test_filtrado_por_evento_y_estado(self):
        """CA2: Verifica que solo se muestren proyectos del evento y con el estado solicitado"""
        self.client.login(username="admin1", password="admin123")

        # Crear otro evento con proyecto rechazado
        otro_evento = Eventos.objects.create(
            eve_nombre="Feria Ambiental",
            eve_descripcion="Conciencia ecológica",
            eve_ciudad="Pereira",
            eve_lugar="Plaza Central",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="image/evento2.jpg",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        Proyecto.objects.create(
            pro_codigo="PRJ002",
            pro_nombre="Reforestando",
            pro_descripcion="Proyecto ecológico",
            pro_documentos="doc.pdf",
            pro_estado="Rechazado",
            pro_fecha_hora=now(),
            pro_evento_fk=otro_evento
        )

        url = reverse("administrador:ver_participantes", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)
        proyectos = response.context["proyectos"]

        self.assertEqual(len(proyectos), 1)
        self.assertEqual(proyectos[0]["pro_nombre"], "Energía Verde")

    def test_contexto_contiene_datos_completos(self):
        """CA3: Verifica que el contexto contenga todos los campos requeridos"""
        self.client.login(username="admin1", password="admin123")
        url = reverse("administrador:ver_participantes", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)

        proyecto = response.context["proyectos"][0]

        # Validar campos clave del contexto
        for campo in ["pro_codigo", "pro_nombre", "documentos", "expositores", "estado"]:
            self.assertIn(campo, proyecto)
