from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

from app_usuarios.models import Usuario
from app_super_admin.models import SuperAdministradores
from app_administrador.models import Administradores
from app_eventos.models import Eventos, ParticipantesEventos, AsistentesEventos, EvaluadoresEventos
from app_participante.models import Participantes
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores, Calificaciones
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_criterios.models import Criterios 

class TestHU94_EstadisticasEvento(TestCase):
    """Suite completa de tests para HU94"""

    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.super_admin_user = Usuario.objects.create_user(
            username='superadmin',
            password='SuperPass123!',
            tipo_documento='CC',
            documento_identidad='1000000001',
            email='superadmin@eventsoft.com'
        )
        self.super_admin = SuperAdministradores.objects.create(usuario=self.super_admin_user)

        self.admin_user = Usuario.objects.create_user(
            username='admin_evento',
            password='AdminPass123!',
            tipo_documento='CC',
            documento_identidad='2000000001',
            email='admin@ejemplo.com'
        )
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado='Activo'
        )

        self.area = Areas.objects.create(
            are_nombre="Tecnología",
            are_descripcion="Área tecnológica"
        )
        self.categoria = Categorias.objects.create(
            cat_nombre="Desarrollo Web",
            cat_descripcion="Desarrollo web",
            cat_area_fk=self.area
        )

        # Crear eventos
        self.evento_con_datos = Eventos.objects.create(
            eve_nombre="Evento con Estadísticas",
            eve_descripcion="Evento con participantes, asistentes y evaluadores",
            eve_ciudad="Bogotá",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=30),
            eve_fecha_fin=timezone.now().date() + timedelta(days=31),
            eve_estado="PUBLICADO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        self.evento_sin_datos = Eventos.objects.create(
            eve_nombre="Evento Sin Datos",
            eve_descripcion="Evento sin participantes ni estadísticas",
            eve_ciudad="Medellín",
            eve_lugar="Teatro",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=40),
            eve_fecha_fin=timezone.now().date() + timedelta(days=41),
            eve_estado="PUBLICADO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        self.evento_comparacion = Eventos.objects.create(
            eve_nombre="Evento para Comparar",
            eve_descripcion="Evento con datos diferentes",
            eve_ciudad="Cali",
            eve_lugar="Universidad",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=50),
            eve_fecha_fin=timezone.now().date() + timedelta(days=51),
            eve_estado="PUBLICADO",
            eve_capacidad=80,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin
        )

        # Crear datos relacionados
        self._crear_participantes_evento()
        self._crear_asistentes_evento()
        self._crear_evaluadores_evento()
        self._crear_calificaciones()

        # Login como super admin
        self.client = Client()
        self.client.login(username='superadmin', password='SuperPass123!')

    # ===========================================================
    # MÉTODOS AUXILIARES (Helpers)
    # ===========================================================

    def _crear_participantes_evento(self):
        """Helper: Crear participantes de prueba"""
        for i in range(5):
            user_participante = Usuario.objects.create_user(
                username=f'participante{i}',
                password='Pass123!',
                tipo_documento='CC',
                documento_identidad=f'300000000{i}',
                email=f'participante{i}@ejemplo.com'
            )
            participante = Participantes.objects.create(usuario=user_participante)

            ParticipantesEventos.objects.create(
                par_eve_evento_fk=self.evento_con_datos,
                par_eve_participante_fk=participante,
                par_eve_fecha_hora=timezone.now(),
                par_eve_documentos=SimpleUploadedFile("proyecto.pdf", b"PDF content"),
                par_eve_estado='APROBADO' if i < 4 else 'PENDIENTE',
                par_eve_qr=SimpleUploadedFile("qr.png", b"QR content"),
                par_eve_clave=f"clave{i}"
            )

    def _crear_asistentes_evento(self):
        """Helper: Crear asistentes de prueba"""
        for i in range(3):
            user_asistente = Usuario.objects.create_user(
                username=f'asistente{i}',
                password='Pass123!',
                tipo_documento='CC',
                documento_identidad=f'400000000{i}',
                email=f'asistente{i}@ejemplo.com'
            )
            asistente = Asistentes.objects.create(usuario=user_asistente)

            AsistentesEventos.objects.create(
                asi_eve_evento_fk=self.evento_con_datos,
                asi_eve_asistente_fk=asistente,
                asi_eve_fecha_hora=timezone.now(),
                asi_eve_estado='CONFIRMADO',
                asi_eve_soporte=SimpleUploadedFile("soporte.pdf", b"PDF content"),
                asi_eve_qr=SimpleUploadedFile("qr.png", b"QR content"),
                asi_eve_clave=f"claveA{i}"
            )

    def _crear_evaluadores_evento(self):
        """Helper: Crear evaluadores de prueba"""
        for i in range(2):
            user_evaluador = Usuario.objects.create_user(
                username=f'evaluador{i}',
                password='Pass123!',
                tipo_documento='CC',
                documento_identidad=f'500000000{i}',
                email=f'evaluador{i}@ejemplo.com'
            )

            evaluador = Evaluadores.objects.create(
                usuario=user_evaluador
            )

            EvaluadoresEventos.objects.create(
                eva_eve_evento_fk=self.evento_con_datos,
                eva_eve_evaluador_fk=evaluador,
                eva_estado='ACTIVO'
            )


    def _crear_calificaciones(self):
        """Helper: Crear calificaciones de prueba"""

        # Crear un criterio válido para el evento
        criterio = Criterios.objects.create(
            cri_descripcion="Calidad del proyecto",
            cri_peso=1.0,
            cri_evento_fk=self.evento_con_datos
        )

        participantes = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=self.evento_con_datos,
            par_eve_estado='APROBADO'
        )

        evaluadores = EvaluadoresEventos.objects.filter(
            eva_eve_evento_fk=self.evento_con_datos
        )

        calificaciones = [85, 90, 78, 92]
        for i, part_evento in enumerate(participantes[:4]):
            if evaluadores.exists():
                Calificaciones.objects.create(
                    cal_evaluador_fk=evaluadores.first().eva_eve_evaluador_fk,
                    cal_criterio_fk=criterio,
                    clas_proyecto_fk=None,  # o un proyecto si quieres asociar uno
                    cal_valor=calificaciones[i],
                    cal_comentario=f"Observación {i}"
                )
    # ===========================================================
    # TESTS PRINCIPALES (ejemplo)
    # ===========================================================

    def test_CA1_super_admin_puede_acceder_panel_estadisticas(self):
        """CA1: SUPER ADMIN debe poder acceder al panel de estadísticas"""
        response = self.client.get(reverse('super_admin:estadisticas_evento',
                                           kwargs={'evento_id': self.evento_con_datos.id}))
        self.assertEqual(response.status_code, 200)

   
