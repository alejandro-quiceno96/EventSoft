from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from app_usuarios.models import Usuario
from app_super_admin.models import SuperAdministradores
 # Ajusta si tu modelo está en otro lado

class AsignarAdminEventoTest(TestCase):

    def setUp(self):
        self.client = Client()
        
        # Crear usuario SuperAdmin autenticado
        self.super_admin = Usuario.objects.create_user(
            username="superadmin",
            password="12345",
            email="superadmin@test.com",
            tipo_documento="CC",
            documento_identidad="111222333"
        )

        self.client.login(username="superadmin", password="12345")

        # Crear usuario que será administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="nuevo_admin",
            password="321",
            email="admin@test.com"
        )

        self.url = reverse('super_admin:asignar_admin_evento')


   

    def test_faltan_campos(self):
        """CA2: Si faltan datos, debe devolver error 400"""
        data = {
            'usuario_id': self.usuario_admin.id,
            'eventos': 3,
            # falta fecha_limite y codigo
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    def test_usuario_no_existe(self):
        """CA3: Si el usuario no existe debe devolver 404"""
        data = {
            'usuario_id': 999999,
            'eventos': 3,
            'fecha_limite': "2025-01-01",
            'codigo': "CODIGO123"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 404)
