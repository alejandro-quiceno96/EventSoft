from django.test import TestCase, Client
from django.urls import reverse
from app_eventos.models import Eventos, EventosCategorias, ParticipantesEventos, EvaluadoresEventos
from app_evaluador.models import Evaluadores
from app_categorias.models import Categorias  # 👈 ajusta el path según tu app real
from app_areas.models import Areas
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
import datetime


class DetalleEventoEvaluadorTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Crear área y categoría (porque cat_area_fk es requerido)
        self.area = Areas.objects.create(
            are_nombre='Ciencias Aplicadas',
            are_descripcion='Área de innovación científica'
        )
        self.categoria = Categorias.objects.create(
            cat_nombre='Innovación',
            cat_descripcion='Categoría de proyectos innovadores',
            cat_area_fk=self.area
        )

        # Crear usuario y evaluador
        self.user = Usuario.objects.create_user(
            username='alejo', password='12345',
            first_name='Alejo', last_name='Tester'
        )
        self.evaluador = Evaluadores.objects.create(usuario=self.user)
        self.admin = Administradores.objects.create(usuario=self.user)
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Evento de Prueba',
            eve_descripcion='Evento para probar cancelación',
            eve_ciudad='Manizales',
            eve_lugar='Centro de Eventos',
            eve_fecha_inicio='2025-11-20',
            eve_fecha_fin='2025-11-22',
            eve_estado='Activo',
            eve_imagen='image/test.png',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin,
        )

        # Relación evento-categoría
        self.evento_categoria = EventosCategorias.objects.create(
            eve_cat_evento_fk=self.evento,
            eve_cat_categoria_fk=self.categoria
        )

        # Relación evento-evaluador
        self.relacion = EvaluadoresEventos.objects.create(
            eva_eve_evento_fk=self.evento,
            eva_eve_evaluador_fk=self.evaluador,
            eva_clave_acceso="123-ABC"
        )

        # URL para la vista
        self.url = reverse('app_evaluador:detalle_evento_evaluador', args=[self.evaluador.id, self.evento.id])

    def test_visualizacion_exitosa_evento(self):
        """CA1: El evaluador puede visualizar la información completa del evento"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_evaluador/detalle_evento.html')
        self.assertContains(response, self.evento.eve_nombre)
        self.assertContains(response, self.evento.eve_descripcion)
        self.assertContains(response, self.categoria.cat_nombre)
        self.assertContains(response, self.relacion.eva_clave_acceso)

    def test_evento_no_existente(self):
        """CA2: Si el evento no existe, retorna 404"""
        url_invalida = reverse('app_evaluador:detalle_evento_evaluador', args=[self.evaluador.id, 9999])
        response = self.client.get(url_invalida)
        self.assertEqual(response.status_code, 404)

    def test_relacion_evento_evaluador_inexistente(self):
        """CA3: Si el evaluador no está inscrito en el evento, no muestra clave de acceso"""
        self.relacion.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "123-ABC")
