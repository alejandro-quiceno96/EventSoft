from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from hashlib import sha256
from app_usuarios.models import Usuario
from app_administrador.models import Administradores


class AsignarAdministradorEventoTest(TestCase):
    """HU-89: Pruebas para la asignación de rol Administrador de Eventos mediante código de acceso"""

    def setUp(self):
        # Crear superusuario que realiza la asignación
        self.super_admin = Usuario.objects.create_superuser(
            username="superadmin",
            password="admin123",
            email="superadmin@test.com",
            tipo_documento="CC",
            documento_identidad="123456789",
        )
        self.client.login(username="superadmin", password="admin123")

        # Crear usuario común que será promovido
        self.usuario_destino = Usuario.objects.create_user(
            username="usuario_evento",
            password="12345",
            email="usuario_evento@test.com",
            tipo_documento="CC",
            documento_identidad="999888777",
        )


        self.url = reverse("super_admin:asignar_admin_evento")

    # ----------------------------------------------------
    # TEST 1: Asignación exitosa
    # ----------------------------------------------------
    
 

    # ----------------------------------------------------
    # TEST 5: Falta un campo obligatorio
    # ----------------------------------------------------
    def test_faltan_campos_obligatorios(self):
        """Debe devolver error si faltan campos en el formulario"""
        data = {
            "usuario_id": "",
            "eventos": "",
            "fecha_limite": "",
            "codigo": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Faltan campos", response.content.decode())

    # ----------------------------------------------------
    # TEST 6: Usuario inexistente
    # ----------------------------------------------------
   