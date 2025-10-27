from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_eventos.models import Eventos
from app_administrador.models import Administradores
from datetime import date

class ConfigurarInscripcionTests(TestCase):
    """HU-56: Habilitar o deshabilitar inscripciones de un evento."""

    def setUp(self):
        # 🔹 Crear usuario administrador
        self.client = Client()

        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111",
            telefono="3000000000"
        )

        # Crear administrador asociado
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # Loguear como administrador
        self.client.force_login(self.usuario_admin)

        # 🔹 Crear evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre="Evento de Prueba",
            eve_descripcion="Evento de prueba para test HU-54",
            eve_ciudad="Manizales",
            eve_lugar="SENA Caldas",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today(),
            eve_estado="Abierto",
            eve_imagen="image/test.jpg",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        self.url = reverse("administrador:configurar_inscripcion", args=[self.evento.id])

    # ----------------------------------------------------------------------

    def test_deshabilitar_inscripcion_participantes(self):
        """✅ Deshabilitar inscripciones de expositores (participantes)"""
        response = self.client.post(
            self.url,
            data={'tipo': 'Expositor', 'estado': False},
            content_type="application/json"
        )
        self.evento.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.evento.eve_habilitar_participantes)
        self.assertIn("Expositor actualizado a False", response.json()["message"])

    # ----------------------------------------------------------------------

    def test_habilitar_inscripcion_evaluadores(self):
        """✅ Habilitar inscripciones de evaluadores"""
        self.evento.eve_habilitar_evaluadores = False
        self.evento.save()

        response = self.client.post(
            self.url,
            data={'tipo': 'Evaluador', 'estado': True},
            content_type="application/json"
        )

        self.evento.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.evento.eve_habilitar_evaluadores)
        self.assertIn("Evaluador actualizado a True", response.json()["message"])

    # ----------------------------------------------------------------------

    def test_metodo_no_permitido(self):
        """🚫 Solo se permite método POST"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn("Método no permitido", response.json()["message"])
