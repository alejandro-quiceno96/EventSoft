from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from app_eventos.models import Eventos, EventosCategorias
from app_administrador.models import Administradores
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_usuarios.models import Usuario

class EdicionEventoTests(TestCase):
    """HU-52: Edición de eventos por Administrador."""

    def setUp(self):
        # Cliente de pruebas
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

        # Crear administrador
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=2,
            estado="Activo",
            clave_acceso="CLV123"
        )

        # Loguear como administrador
        self.client.force_login(self.usuario_admin)

        # Crear área y categoría
        self.area = Areas.objects.create(
            are_nombre="Tecnología",
            are_descripcion="Área de tecnología"
        )
        self.categoria = Categorias.objects.create(
            cat_nombre="Conferencia",
            cat_descripcion="Descripción conferencia",
            cat_area_fk=self.area
        )

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Original",
            eve_descripcion="Descripción",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today() + timedelta(days=1),
            eve_capacidad=100,
            eve_tienecosto=True,
            eve_estado="Abierto",
            eve_administrador_fk=self.admin
        )

        # Asociar categoría al evento
        self.evento_categoria = EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento,
            eve_cat_categoria_fk=self.categoria
        )

        # URL de edición
        self.url_editar = reverse('administrador:editar_evento', args=[self.evento.id])

    def test_editar_evento(self):
        """El administrador puede editar la información del evento si está abierto."""
        data = {
            'nombre_evento': 'Evento Editado',
            'descripcion_evento': self.evento.eve_descripcion,
            'ciudad': self.evento.eve_ciudad,
            'lugar': self.evento.eve_lugar,
            'fecha_inicio': self.evento.eve_fecha_inicio.isoformat(),
            'fecha_fin': self.evento.eve_fecha_fin.isoformat(),
            'categoria': self.categoria.id,
            'inscripcion': 'Si',
            'estado_evento': self.evento.eve_estado,
            'cantidad_personas': self.evento.eve_capacidad
        }
        response = self.client.post(self.url_editar, data)

        # Refrescar evento desde DB
        self.evento.refresh_from_db()
        self.evento_categoria.refresh_from_db()

        # Comprobaciones
        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(self.evento.eve_nombre, "Evento Editado")
        self.assertEqual(self.evento_categoria.eve_cat_categoria_fk.id, self.categoria.id)

    def test_no_editar_evento_cerrado(self):
        """No se puede editar un evento si está cerrado."""
        self.evento.eve_estado = "Cerrado"
        self.evento.save()

        data = {
            'nombre_evento': 'Intento Editar',
            'descripcion_evento': self.evento.eve_descripcion,
            'ciudad': self.evento.eve_ciudad,
            'lugar': self.evento.eve_lugar,
            'fecha_inicio': self.evento.eve_fecha_inicio.isoformat(),
            'fecha_fin': self.evento.eve_fecha_fin.isoformat(),
            'categoria': self.categoria.id,
            'inscripcion': 'Si',
            'estado_evento': self.evento.eve_estado,
            'cantidad_personas': self.evento.eve_capacidad
        }
        response = self.client.post(self.url_editar, data)

        # Refrescar evento desde DB
        self.evento.refresh_from_db()

        # Verificar que el nombre NO se haya modificado
        self.assertNotEqual(self.evento.eve_nombre, "Intento Editar")
        # La vista redirige al index con mensaje de error
        self.assertEqual(response.status_code, 302)
