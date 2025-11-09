from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from app_administrador.models import Administradores
from app_eventos.models import Eventos, AsistentesEventos, EvaluadoresEventos, ParticipantesEventos
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores
from app_participante.models import Participantes
from app_usuarios.models import Usuario as User

class HU73EstadisticasEventoTestCase(TestCase):
    """Pruebas de la historia HU73 - Obtener información estadística sobre un evento"""

    def setUp(self):
        self.client = Client()

        # Crear usuario administrador
        self.user_admin = User.objects.create_user(
            username='admin_hu73',
            password='12345',
            first_name='Admin',
            last_name='Eventos'
        )
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento principal
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Principal',
            eve_descripcion='Evento de prueba HU73',
            eve_ciudad='Manizales',
            eve_lugar='Centro',
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado='Activo',
            eve_imagen='image/test.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear segundo evento sin registros
        self.evento_vacio = Eventos.objects.create(
            eve_nombre='Evento Vacío',
            eve_descripcion='Sin registros',
            eve_ciudad='Pereira',
            eve_lugar='Auditorio',
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado='Activo',
            eve_imagen='image/test2.jpg',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear usuarios asociados y registros
        self.user_asistente = User.objects.create_user(username='asistente1', password='12345')
        asistente = Asistentes.objects.create(usuario=self.user_asistente)
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte='pdf/test.pdf',
            asi_eve_qr='pdf/qr_asistentes/test.pdf',
            asi_eve_clave='ABC123'
        )

        self.user_participante = User.objects.create_user(username='participante1', password='12345')
        participante = Participantes.objects.create(usuario=self.user_participante)
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=participante,
            par_eve_evento_fk=self.evento,
            par_eve_fecha_hora=now(),
            par_eve_documentos='pdf/proyecto.pdf',
            par_eve_estado='Admitido',
            par_eve_qr='pdf/qr_participante/test.pdf',
            par_eve_clave='XYZ987'
        )

        self.user_evaluador = User.objects.create_user(username='evaluador1', password='12345')
        evaluador = Evaluadores.objects.create(usuario=self.user_evaluador)
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=evaluador,
            eva_eve_evento_fk=self.evento,
            eva_estado='Admitido',
            eva_clave_acceso='CLV123'
        )

        self.client.login(username='admin_hu73', password='12345')
        self.url = reverse('administrador:index_administrador')

    def test_estadisticas_evento_con_datos(self):
        """CA1 y CA2: Verifica que los totales por evento sean correctos."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        eventos = response.context['eventos']

        evento = next((e for e in eventos if e.id == self.evento.id), None)
        self.assertIsNotNone(evento)
        self.assertEqual(evento.total_asistentes, 1)
        self.assertEqual(evento.total_participantes, 1)
        self.assertEqual(evento.total_evaluadores, 1)
        self.assertEqual(evento.total_inscritos, 3)

    def test_evento_sin_datos_muestra_ceros(self):
        """CA3: Verifica que los eventos sin registros muestren totales en 0."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        eventos = response.context['eventos']

        evento_vacio = next((e for e in eventos if e.id == self.evento_vacio.id), None)
        self.assertIsNotNone(evento_vacio)
        self.assertEqual(evento_vacio.total_asistentes, 0)
        self.assertEqual(evento_vacio.total_participantes, 0)
        self.assertEqual(evento_vacio.total_evaluadores, 0)
        self.assertEqual(evento_vacio.total_inscritos, 0)

    def test_informacion_en_contexto_para_modal(self):
        """CA4: Verifica que los datos estén en el contexto (para mostrar en el modal)."""
        response = self.client.get(self.url)
        self.assertIn('eventos', response.context)
        for evento in response.context['eventos']:
            self.assertTrue(hasattr(evento, 'total_asistentes'))
            self.assertTrue(hasattr(evento, 'total_participantes'))
            self.assertTrue(hasattr(evento, 'total_evaluadores'))
            self.assertTrue(hasattr(evento, 'total_inscritos'))
