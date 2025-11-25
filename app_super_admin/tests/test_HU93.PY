from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from app_usuarios.models import Usuario
from app_super_admin.models import SuperAdministradores
from app_administrador.models import Administradores
from app_eventos.models import Eventos
from app_areas.models import Areas
from app_categorias.models import Categorias


class TestHU93_PublicarEventoSitioWeb(TestCase):
    """Suite completa de tests para HU93"""

    def setUp(self):
        """Configuración inicial para todos los tests"""

        # Crear usuario super administrador
        self.super_admin_user = Usuario.objects.create_user(
            username='superadmin',
            password='SuperPass123!',
            tipo_documento='CC',
            documento_identidad='1000000001',
            email='superadmin@eventsoft.com'
        )

        # Crear registro de super administrador
        self.super_admin = SuperAdministradores.objects.create(
            usuario=self.super_admin_user
        )

        # Crear usuario administrador
        self.admin_user = Usuario.objects.create_user(
            username='admin_evento',
            password='AdminPass123!',
            tipo_documento='CC',
            documento_identidad='2000000001',
            email='admin@ejemplo.com'
        )

        # Crear registro de administrador
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado='Activo'
        )

        # Crear evento completo
        self.evento_completo = Eventos.objects.create(
            eve_nombre="Evento Completo para Publicar",
            eve_descripcion="Evento con todos los campos completos",
            eve_ciudad="Bogotá",
            eve_lugar="Centro de Convenciones",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=30),
            eve_fecha_fin=timezone.now().date() + timedelta(days=31),
            eve_estado="BORRADOR",
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )

        # Crear evento incompleto
        self.evento_incompleto = Eventos.objects.create(
            eve_nombre="Evento Incompleto",
            eve_descripcion="",
            eve_ciudad="Bogotá",
            eve_lugar="",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=10),
            eve_fecha_fin=timezone.now().date() + timedelta(days=11),
            eve_estado="BORRADOR",
            eve_capacidad=0,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Crear evento ya publicado
        self.evento_publicado = Eventos.objects.create(
            eve_nombre="Evento Publicado",
            eve_descripcion="Evento de prueba ya publicado",
            eve_ciudad="Medellín",
            eve_lugar="Plaza Mayor",
            eve_fecha_inicio=timezone.now().date() + timedelta(days=15),
            eve_fecha_fin=timezone.now().date() + timedelta(days=16),
            eve_estado="PUBLICADO",
            eve_capacidad=150,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Cliente autenticado como superadmin
        self.client = Client()
        self.client.login(username='superadmin', password='SuperPass123!')

    # ============================================================================
    # CRITERIO 1: Publicación y visibilidad inmediata
    # ============================================================================

    def test_CA1_super_admin_puede_publicar_evento_completo(self):
        """CA1: Super admin puede cambiar estado de BORRADOR a PUBLICADO"""
        self.assertEqual(self.evento_completo.eve_estado, 'BORRADOR')
        response = self.client.post(
            reverse('super_admin:modificar_eventos', kwargs={
                'evento_id': self.evento_completo.id,
                'nuevo_estado': 'PUBLICADO'
            }),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.evento_completo.refresh_from_db()
        self.assertEqual(self.evento_completo.eve_estado, 'PUBLICADO')


    def test_CA1_evento_borrador_no_visible_para_visitantes(self):
        """CA1: Evento en BORRADOR NO debe ser visible para visitantes"""
        visitante = Client()
        response = visitante.get(reverse('inicio_visitante'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.evento_completo.eve_nombre)


    def test_CA1_visitante_no_puede_ver_detalle_evento_borrador(self):
        """CA1: Visitantes NO deben poder ver el detalle de evento en borrador"""
        visitante = Client()
        response = visitante.get(reverse('detalle_evento', kwargs={'evento_id': self.evento_completo.id}))
        self.assertIn(response.status_code, [403, 404, 302])


    # ============================================================================
    # CRITERIO 3: Revertir de PUBLICADO a BORRADOR
    # ============================================================================

    def test_CA3_super_admin_puede_revertir_publicado_a_borrador(self):
        """CA3: Super admin debe poder revertir PUBLICADO → BORRADOR"""
        response = self.client.post(
            reverse('super_admin:modificar_eventos', kwargs={
                'evento_id': self.evento_publicado.id,
                'nuevo_estado': 'BORRADOR'
            }),
            follow=True
        )
        self.evento_publicado.refresh_from_db()
        self.assertEqual(self.evento_publicado.eve_estado, 'BORRADOR')

    def test_CA3_evento_revertido_no_visible_para_visitantes(self):
        """CA3: Evento revertido a BORRADOR no debe mostrarse públicamente"""
        self.evento_publicado.eve_estado = 'BORRADOR'
        self.evento_publicado.save()
        visitante = Client()
        response = visitante.get(reverse('inicio_visitante'))
        self.assertNotContains(response, self.evento_publicado.eve_nombre)

    # ============================================================================
    # SEGURIDAD Y VALIDACIONES ADICIONALES
    # ============================================================================

    def test_solo_super_admin_puede_publicar_eventos(self):
        """Seguridad: Solo SUPER ADMIN puede publicar"""
        self.client.logout()
        self.client.login(username='admin_evento', password='AdminPass123!')
        response = self.client.post(
            reverse('super_admin:modificar_eventos', kwargs={
                'evento_id': self.evento_completo.id,
                'nuevo_estado': 'PUBLICADO'
            })
        )
        self.assertIn(response.status_code, [302, 403])

