from django.test import TestCase, Client
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes
from app_usuarios.models import Usuario
from datetime import date

class AsistentesAdmitidosTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        usuario_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9999",
            telefono="3100000000"
        )

        # Crear administrador
        self.admin = Administradores.objects.create(
            usuario=usuario_admin,
            num_eventos=1,
            estado="Activo",
            clave_acceso="CLVADMIN"
        )

        self.client.force_login(usuario_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Expo Tecnología",
            eve_descripcion="Evento de innovación",
            eve_ciudad="Manizales",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=date(2025, 10, 1),
            eve_fecha_fin=date(2025, 10, 3),
            eve_estado="Activo",
            eve_imagen="image/test.jpg",
            eve_capacidad=100,
            eve_administrador_fk=self.admin
        )

        # Crear usuarios asistentes y su registro como Asistentes
        usuario_asistente1 = Usuario.objects.create_user(
            username='asistente1',
            password='12345',
            first_name='Juan',
            email='juan1@example.com'
        )
        usuario_asistente2 = Usuario.objects.create_user(
            username='asistente2',
            password='12345',
            first_name='Juan2',
            email='juan2@example.com'
        )
        usuario_asistente3 = Usuario.objects.create_user(
            username='asistente3',
            password='12345',
            first_name='Juan3',
            email='juan3@example.com'
        )

        # Crear instancias de Asistentes
        # Crear instancias de Asistentes
        self.asistente1 = Asistentes.objects.create(usuario=usuario_asistente1)
        self.asistente2 = Asistentes.objects.create(usuario=usuario_asistente2)
        self.asistente3 = Asistentes.objects.create(usuario=usuario_asistente3)


        # Crear registros de AsistentesEventos
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente1,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Admitido",
            asi_eve_soporte="pdf/comprobantes/test1.pdf",
            asi_eve_qr="pdf/qr_asistentes/qr1.pdf",
            asi_eve_clave="A123"
        )

        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente2,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Pendiente",
            asi_eve_soporte="pdf/comprobantes/test2.pdf",
            asi_eve_qr="pdf/qr_asistentes/qr2.pdf",
            asi_eve_clave="B456"
        )

        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente3,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Admitido",
            asi_eve_soporte="pdf/comprobantes/test3.pdf",
            asi_eve_qr="pdf/qr_asistentes/qr3.pdf",
            asi_eve_clave="C789"
        )

    def test_contar_asistentes_admitidos(self):
        """Debe contar correctamente los asistentes admitidos para un evento."""
        total_admitidos = AsistentesEventos.objects.filter(
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="Admitido"
        ).count()

        self.assertEqual(total_admitidos, 2, "Debe haber 2 asistentes admitidos")



