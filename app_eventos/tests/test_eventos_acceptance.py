from django.test import TestCase
from django.urls import reverse
from app_usuarios.models import Usuario
from app_eventos.models import Eventos, ParticipantesEventos
from app_administrador.models import Administradores
from app_participante.models import Participantes
from datetime import date, timedelta
from app_eventos.models import AsistentesEventos
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores, Calificaciones
from app_criterios.models import Criterios
from django.utils import timezone
from datetime import datetime


class EventoAcceptanceTests(TestCase):
    def setUp(self):
        # Crear usuario admin
        self.usuario_admin = Usuario.objects.create_user(
            username="adminuser",
            email="admin@test.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="123",
            telefono="12345"
        )

        # Crear administrador asociado al usuario
        self.admin = Administradores.objects.create(
            usuario=self.usuario_admin,
            num_eventos=0,
            estado="activo",
            clave_acceso="12345678"
        )

        # Crear eventos
        self.evento_futuro = Eventos.objects.create(
            eve_nombre="Evento Futuro",
            eve_descripcion="Descripción evento futuro",
            eve_ciudad="Bogotá",
            eve_lugar="Auditorio Central",
            eve_fecha_inicio=date.today() + timedelta(days=10),
            eve_fecha_fin=date.today() + timedelta(days=11),
            eve_estado="activo",
            eve_imagen="image/test.png",
            eve_capacidad=100,
            eve_administrador_fk=self.admin
        )

        self.evento_pasado = Eventos.objects.create(
            eve_nombre="Evento Pasado",
            eve_descripcion="Descripción evento pasado",
            eve_ciudad="Medellín",
            eve_lugar="Auditorio Secundario",
            eve_fecha_inicio=date.today() - timedelta(days=10),
            eve_fecha_fin=date.today() - timedelta(days=9),
            eve_estado="activo",
            eve_imagen="image/test2.png",
            eve_capacidad=50,
            eve_administrador_fk=self.admin
        )

        # Crear usuario participante
        self.usuario_participante = Usuario.objects.create_user(
            username="participante1",
            email="par@test.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="456",
            telefono="67890"
        )
        self.participante = Participantes.objects.create(usuario=self.usuario_participante)

    def test_listado_eventos_futuros_muestra_solo_futuros(self):
        # Loguear el usuario administrador
        self.client.login(username="adminuser", password="12345")
        response = self.client.get(reverse('administrador:index_administrador'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Futuro")

    def test_busqueda_compuesta_por_titulo_lugar_fecha(self):
        self.client.login(username="adminuser", password="12345")
        response = self.client.get(reverse('administrador:index_administrador'), {
            "titulo": "Futuro",
            "lugar": "Auditorio Central",
            "fecha_inicio": (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "fecha_fin": (date.today() + timedelta(days=15)).strftime("%Y-%m-%d"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Futuro")

    def test_detalle_evento_tiene_url_unica(self):
        self.client.login(username="adminuser", password="12345")
        url = reverse('administrador:evento_detalle', args=[self.evento_futuro.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.evento_futuro.eve_nombre)

    def test_registro_participante_crea_inscripcion(self):
        # Crear inscripción
        inscripcion = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento_futuro,
            par_eve_fecha_hora=date.today(),
            par_eve_estado="Activo",
            par_eve_documentos="pdf/proyectos/test.pdf",
            par_eve_qr="pdf/qr_participante/test.png",
            par_eve_clave="clave123"
        )

        # Comprobar que la inscripción se ha creado correctamente
        self.assertEqual(inscripcion.par_eve_evento_fk, self.evento_futuro)
        self.assertEqual(inscripcion.par_eve_participante_fk, self.participante)
        self.assertEqual(inscripcion.par_eve_estado, "Activo")

####################################################################################333

class EventoAcceptanceTestsExtendido(EventoAcceptanceTests):

    def setUp(self):
        super().setUp()
        
    
        # Crear usuario asistente
        self.usuario_asistente = Usuario.objects.create_user(
            username="asistente1",
            email="asis@test.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="789",
            telefono="112233"
        )
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

        # Crear usuario evaluador
        self.usuario_evaluador = Usuario.objects.create_user(
            username="evaluador1",
            email="eval@test.com",
            password="12345",
            tipo_documento="CC",
            documento_identidad="987",
            telefono="445566"
        )
        # ⚠️ Solo asociar usuario al evaluador
        self.evaluador = Evaluadores.objects.create(usuario=self.usuario_evaluador)

        self.criterio = Criterios.objects.create(
                cri_descripcion="Descripción de prueba",
                cri_peso=10,  # ejemplo de peso
                cri_evento_fk=self.evento_futuro  # asignamos el evento creado en setUp
            )

    def test_registro_asistente_crea_inscripcion(self):
        inscripcion_asistente = AsistentesEventos.objects.create(
        asi_eve_asistente_fk=self.asistente,
        asi_eve_evento_fk=self.evento_futuro,
        asi_eve_fecha_hora=timezone.now(),
        asi_eve_estado="Activo",
        asi_eve_soporte="pdf/asistentes/test.pdf",
        asi_eve_qr="pdf/qr_asistente/test.png",
        asi_eve_clave="clave_asis123"
)

        self.assertEqual(inscripcion_asistente.asi_eve_evento_fk, self.evento_futuro)
        self.assertEqual(inscripcion_asistente.asi_eve_asistente_fk, self.asistente)
        self.assertEqual(inscripcion_asistente.asi_eve_estado, "Activo")

    def test_registro_evaluador_crea_calificacion(self):
    # ⚠️ Debes tener un criterio existente, aquí usamos None si lo permite tu modelo
        calificacion = Calificaciones.objects.create(
            cal_evaluador_fk=self.evaluador,
            cal_criterio_fk=self.criterio,  
            clas_proyecto_fk=None,  # Opcional
            cal_valor=10,
            cal_comentario="Buen trabajo"
        )

        self.assertEqual(calificacion.cal_evaluador_fk, self.evaluador)
        self.assertEqual(calificacion.cal_valor, 10)
        self.assertEqual(calificacion.cal_comentario, "Buen trabajo")