from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now

from app_eventos.models import Eventos, EvaluadoresEventos 
from app_administrador.models import Administradores
from app_evaluador.models import Evaluadores # Asegúrate que estos modelos existan
from app_usuarios.models import Usuario as User

class VerEvaluadoresAceptadosTestCase(TestCase):
    """
    HU64 - ADMINISTRADOR EVENTO:
    Ver los datos de los evaluadores aceptados en un evento y su documentación aportada.
    """

    def setUp(self):
        """Configuración inicial de datos para las pruebas"""
        self.client = Client()

        # Crear usuario administrador
        self.user_admin = User.objects.create_user(
            username="admin1",
            password="admin123",
            first_name="Carlos",
            last_name="López",
            is_staff=True
        )

        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Ciencia 2025",
            eve_descripcion="Evento de innovación científica",
            eve_ciudad="Manizales",
            eve_lugar="Centro Cultural",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear usuarios evaluadores
        self.user_eval_1 = User.objects.create_user(
            username="eval1",
            password="1234",
            first_name="Laura",
            last_name="Gómez",
            email="laura@example.com"
        )
        self.user_eval_2 = User.objects.create_user(
            username="eval2",
            password="1234",
            first_name="Pedro",
            last_name="Martínez",
            email="pedro@example.com"
        )

        # Crear objetos Evaluadores
        self.evaluador1 = Evaluadores.objects.create(usuario=self.user_eval_1)
        self.evaluador2 = Evaluadores.objects.create(usuario=self.user_eval_2)

        # Crear relación evento-evaluadores
        self.evaluador_evento_1 = EvaluadoresEventos.objects.create(
            eva_eve_evento_fk=self.evento,
            eva_eve_evaluador_fk=self.evaluador1,
            eva_estado="Aceptado",
            eva_eve_documentos="documento1.pdf",
            eva_eve_areas_interes="Ciencias Naturales",
            eva_eve_fecha_hora=now()
        )

        self.evaluador_evento_2 = EvaluadoresEventos.objects.create(
            eva_eve_evento_fk=self.evento,
            eva_eve_evaluador_fk=self.evaluador2,
            eva_estado="Rechazado",
            eva_eve_documentos="documento2.pdf",
            eva_eve_areas_interes="Tecnología",
            eva_eve_fecha_hora=now()
        )

    # -------------------------------------------------------------
    # TESTS
    # -------------------------------------------------------------

    def test_acceso_autenticado(self):
        """CA1: El administrador autenticado puede acceder correctamente"""
        self.client.login(username="admin1", password="admin123")

        url = reverse("administrador:ver_evaluadores", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_administrador/ver_evaluadores.html")
        self.assertIn("evaluadores", response.context)

    def test_filtrado_por_estado(self):
        """CA2: Solo se muestran los evaluadores con el estado solicitado"""
        self.client.login(username="admin1", password="admin123")

        url = reverse("administrador:ver_evaluadores", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)
        evaluadores = response.context["evaluadores"]

        self.assertEqual(len(evaluadores), 1)
        self.assertEqual(evaluadores[0]["eva_nombre"], "Laura Gómez")
        self.assertEqual(evaluadores[0]["estado"], "Aceptado")

    def test_contexto_completo(self):
        """CA3: El contexto contiene todos los campos requeridos"""
        self.client.login(username="admin1", password="admin123")

        url = reverse("administrador:ver_evaluadores", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)
        evaluador = response.context["evaluadores"][0]

        for campo in ["eva_id", "eva_nombre", "eva_correo", "eva_telefono", "estado", "documento", "area_evaluar", "hora_inscripcion"]:
            self.assertIn(campo, evaluador)

    def test_sin_evaluadores_en_estado(self):
        """CA4: Si no hay evaluadores en el estado solicitado, la lista debe estar vacía"""
        self.client.login(username="admin1", password="admin123")

        url = reverse("administrador:ver_evaluadores", args=[self.evento.id]) + "?estado=Pendiente"
        response = self.client.get(url)

        evaluadores = response.context["evaluadores"]
        self.assertEqual(len(evaluadores), 0)

    def test_acceso_no_autenticado(self):
        """CA5: Si no está autenticado, redirige al login"""
        url = reverse("administrador:ver_evaluadores", args=[self.evento.id]) + "?estado=Aceptado"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)
