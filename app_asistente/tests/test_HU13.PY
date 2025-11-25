# app_asistente/tests/HU-13.py
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.base import ContentFile
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_usuarios.models import Usuario
from django.utils import timezone
from datetime import timedelta
from app_administrador.models import Administradores


class DescargaMemoriasTests(TestCase):
    """✅ HU-13: Descarga de memorias del evento por los asistentes"""

    def setUp(self):
        self.client = Client()

        # Crear administrador
        self.usuario_admin = Usuario.objects.create_user(
            username="admin1",
            email="admin@example.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="1001",
            telefono="3000000001"
        )
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=0,
            estado="Activo",
            clave_acceso="ABCD1234"
        )

        # Crear usuario asistente activo
        self.usuario_asistente_activo = Usuario.objects.create_user(
            username="asistente_activo",
            email="activo@example.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="2002",
            telefono="3000000002"
        )

        # Crear usuario asistente inactivo
        self.usuario_asistente_inactivo = Usuario.objects.create_user(
            username="asistente_inactivo",
            email="inactivo@example.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="2003",
            telefono="3000000003"
        )

        # Crear asistentes
        self.asistente_activo = Asistentes.objects.create(usuario=self.usuario_asistente_activo)
        self.asistente_inactivo = Asistentes.objects.create(usuario=self.usuario_asistente_inactivo)

        # Crear evento sin memorias inicialmente
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Futuro",
            eve_fecha_inicio=timezone.now() + timedelta(days=3),
            eve_fecha_fin=timezone.now() + timedelta(days=5),
            eve_capacidad=10,
            eve_estado="Abierto",
            eve_administrador_fk=self.admin
        )

        # Relacionar asistentes con el evento y asignar estado
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente_activo,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Admitido",
            asi_eve_fecha_hora=timezone.now()
        )
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente_inactivo,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Rechazado",
            asi_eve_fecha_hora=timezone.now()
        )

        # Crear archivo de memoria simulado
        self.memoria_pdf = ContentFile(b"Contenido del PDF", name="memoria.pdf")

        # URL de descarga
        self.url_memorias = reverse('app_asistente:descargar_memorias', args=[self.evento.id])

    def test_asistente_activo_puede_descargar_memorias(self):
        """✅ El asistente activo puede acceder y descargar las memorias del evento."""
        # Simular URL de memoria
        self.evento.eve_memorias = "http://example.com/memoria.pdf"
        self.evento.save()

        self.client.login(username="asistente_activo", password="12345")
        response = self.client.get(self.url_memorias)

        # Comprobar que redirige a la URL correcta
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], "http://example.com/memoria.pdf")

    def test_asistente_inactivo_no_ve_opcion_descarga(self):
        """✅ El asistente inactivo no debe ver la opción de descarga."""
        # Guardar PDF en el evento
        self.evento.eve_memorias = self.memoria_pdf
        self.evento.save()

        # Loguear al usuario inactivo
        self.client.login(username="asistente_inactivo", password="12345")

        response = self.client.get(self.url_memorias)
        self.assertEqual(response.status_code, 403)
        print("✔️ El asistente inactivo no puede ver ni descargar las memorias.")

    def test_mensaje_si_no_hay_memorias(self):
        """✅ Si no hay memorias cargadas, debe mostrarse mensaje informativo."""
        # Asegurarse de que no haya memorias
        self.evento.eve_memorias = None
        self.evento.save()

        # Loguear al usuario activo
        self.client.login(username="asistente_activo", password="12345")

        response = self.client.get(self.url_memorias)
        self.assertContains(response, "Las memorias aún no están disponibles", status_code=200)
        print("✔️ Muestra correctamente el mensaje cuando no hay memorias disponibles.")
