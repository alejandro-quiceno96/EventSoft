from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_usuarios.models import Usuario
from app_asistente.models import Asistentes


class RegistroEventoTest(TestCase):

    def setUp(self):
        # Crear usuario visitante y su asistente
        self.usuario = Usuario.objects.create_user(
            username="visitante_test",
            password="testpass123",
            tipo_documento="CC",
            documento_identidad="111111111",
            email="visitante@test.com"
        )
        self.asistente = Asistentes.objects.create(usuario=self.usuario)

        # Crear administrador
        self.admin_user = Usuario.objects.create_user(
            username="admin_test",
            password="adminpass123",
            tipo_documento="CC",
            documento_identidad="222222222",
            email="admin@test.com"
        )
        self.admin = Administradores.objects.create(usuario=self.admin_user)

        # Crear evento gratuito con cupos
        self.evento = Eventos.objects.create(
            eve_nombre="Evento de Registro",
            eve_descripcion="Evento de prueba con registro gratuito.",
            eve_ciudad="Medellín",
            eve_lugar="Parque Central",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=5),
            eve_fecha_fin=timezone.now().date() + timedelta(days=6),
            eve_estado="Activo",
            eve_imagen="image/evento3.png",
            eve_capacidad=2,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
            eve_programacion="pdf/programacion/evento3.pdfñ"
        )

    def test_registro_exitoso_con_cupo(self):
        """Registro válido debe admitir al asistente y disminuir cupos"""
        self.client.login(username="visitante_test", password="testpass123")

        url = reverse("registrar_asistente", args=[self.evento.id])
        response = self.client.post(url)


        inscripcion = AsistentesEventos.objects.get(
            asi_eve_asistente_fk=self.asistente.id,
            asi_eve_evento_fk=self.evento.id
        )
        
        # Debe crear inscripción y estar en estado "Admitido"
        self.assertEqual(inscripcion.asi_eve_estado, "Admitido")

        # Cupo debe disminuir
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.eve_capacidad, 1)

        # Confirma que en la respuesta aparezca algo del evento
        self.assertRedirects( response, reverse("inicio_visitante") + "?registro=exito_asistente"
)


    def test_registro_sin_cupos(self):
        """Si no hay cupos, no se debe registrar y debe mostrar mensaje"""
        self.evento.eve_capacidad = 0
        self.evento.save()

        self.client.login(username="visitante_test", password="testpass123")

        url = reverse("registrar_asistente", args=[self.evento.id])
        response = self.client.post(url)

        # No debe crear inscripción
        self.assertFalse(AsistentesEventos.objects.filter(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento
        ).exists())

        # Cupo sigue en 0
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.eve_capacidad, 0)

        self.assertRedirects(response, reverse("detalle_evento", args=[self.evento.id]))


    def test_registro_concurrencia(self):
        """Debe controlar concurrencia para evitar sobreinscripciones"""
        # Simular un evento con 1 solo cupo
        self.evento.eve_capacidad = 1
        self.evento.save()

        # Crear 2 asistentes que intentarán inscribirse
        for i in range(2):
            user = Usuario.objects.create_user(
                username=f"user_{i}",
                password="testpass123",
                tipo_documento="CC",
                documento_identidad=f"33333333{i}",
                email=f"user{i}@test.com"
            )
            asistente = Asistentes.objects.create(usuario=user)
            self.client.login(username=user.username, password="testpass123")
            self.client.post(reverse("registrar_asistente", args=[self.evento.id]))

        # Refrescar datos del evento desde la BD
        self.evento.refresh_from_db()

        # ✅ Validar que la capacidad nunca sea negativa
        self.assertGreaterEqual(self.evento.eve_capacidad, 0)

        # ✅ Validar que solo se registró UN asistente, porque el cupo era 1
        self.assertEqual(
            AsistentesEventos.objects.filter(asi_eve_evento_fk=self.evento).count(),
            1
        )

        # ✅ Validar que el cupo del evento ahora es 0
        self.assertEqual(self.evento.eve_capacidad, 0)

