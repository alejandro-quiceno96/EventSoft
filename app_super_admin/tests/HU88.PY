from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores


class CrearEventoViewTest(TestCase):
    """HU-88: Pruebas para creación de eventos por un administrador con límite"""

    def setUp(self):
        # Crear usuario administrador y su perfil
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_eventos",
            password="admin123",
            email="admin_eventos@example.com",
        )
        self.admin = Administradores.objects.create(usuario=self.usuario_admin, num_eventos=5)

        # Iniciar sesión antes de cada prueba
        self.client.login(username="admin_eventos", password="admin123")

    # ---------------------------------------------
    # TEST 1: Creación exitosa
    # ---------------------------------------------
   

    # ---------------------------------------------
    # TEST 2: Supera el límite de eventos
    # ---------------------------------------------
    def test_rechaza_evento_si_supera_limite(self):
        """CA2: Debe rechazar creación si supera el número máximo permitido"""
        for i in range(self.admin.num_eventos):
            Eventos.objects.create(
                eve_nombre=f"Evento {i+1}",
                eve_descripcion="Evento de prueba",
                eve_fecha_inicio=timezone.now().date() + timedelta(days=i),
                eve_fecha_fin=timezone.now().date() + timedelta(days=i+1),
                eve_capacidad=100,
                eve_estado="BORRADOR",
                eve_administrador_fk=self.admin,
            )

        data = {
            "eve_nombre": "Evento Excedente",
            "eve_descripcion": "Este evento no debería crearse",
            "eve_fecha_inicio": (timezone.now().date() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "eve_fecha_fin": (timezone.now().date() + timedelta(days=11)).strftime("%Y-%m-%d"),
            "eve_capacidad": 150,
        }

        response = self.client.post(reverse("administrador:crear_evento"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Eventos.objects.filter(eve_nombre="Evento Excedente").exists())

    # ---------------------------------------------
    # TEST 3: Fechas inválidas
    # ---------------------------------------------
    def test_rechaza_evento_con_fechas_invalidas(self):
        """CA3: Debe rechazar si la fecha de fin es anterior a la de inicio"""
        data = {
            "eve_nombre": "Evento Fechas Incorrectas",
            "eve_descripcion": "Evento con fechas inválidas",
            "eve_fecha_inicio": (timezone.now().date() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "eve_fecha_fin": (timezone.now().date() + timedelta(days=9)).strftime("%Y-%m-%d"),
            "eve_capacidad": 100,
        }

        response = self.client.post(reverse("administrador:crear_evento"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Eventos.objects.filter(eve_nombre="Evento Fechas Incorrectas").exists())

    # ---------------------------------------------
    # TEST 4: Datos incompletos
    # ---------------------------------------------
    def test_rechaza_evento_con_datos_incompletos(self):
        """CA4: Debe rechazar si faltan campos obligatorios"""
        data = {
            "eve_nombre": "",
            "eve_descripcion": "",
            "eve_fecha_inicio": "",
            "eve_fecha_fin": "",
            "eve_capacidad": "",
        }

        response = self.client.post(reverse("administrador:crear_evento"), data)
        self.assertEqual(response.status_code, 200)

    # ---------------------------------------------
    # TEST 5: Fecha de inicio en el pasado
    # ---------------------------------------------
    def test_rechaza_evento_con_fecha_inicio_pasada(self):
        """CA adicional: No debe permitir crear eventos con fecha de inicio en el pasado"""
        data = {
            "eve_nombre": "Evento Fecha Pasada",
            "eve_descripcion": "Evento con fecha en el pasado",
            "eve_fecha_inicio": (timezone.now().date() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "eve_fecha_fin": (timezone.now().date() - timedelta(days=4)).strftime("%Y-%m-%d"),
            "eve_capacidad": 150,
        }

        response = self.client.post(reverse("administrador:crear_evento"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Eventos.objects.filter(eve_nombre="Evento Fecha Pasada").exists())

    # ---------------------------------------------
    # TEST 6: Capacidad inválida
    # ---------------------------------------------
    def test_rechaza_evento_con_capacidad_invalida(self):
        """CA adicional: La capacidad debe ser un número positivo"""
        data = {
            "eve_nombre": "Evento Capacidad Inválida",
            "eve_descripcion": "Evento con capacidad negativa",
            "eve_fecha_inicio": (timezone.now().date() + timedelta(days=15)).strftime("%Y-%m-%d"),
            "eve_fecha_fin": (timezone.now().date() + timedelta(days=16)).strftime("%Y-%m-%d"),
            "eve_capacidad": -50,
        }

        response = self.client.post(reverse("administrador:crear_evento"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Eventos.objects.filter(eve_nombre="Evento Capacidad Inválida").exists())

    # ---------------------------------------------
    # TEST 7: Estado inicial del evento
    # ---------------------------------------------



    # ---------------------------------------------
    # TEST 8: Asociación con el administrador
    # ---------------------------------------------
    

     
