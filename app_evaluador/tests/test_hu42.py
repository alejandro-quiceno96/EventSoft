from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from app_eventos.models import Eventos
from app_criterios.models import Criterios
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User 
import json


class GestionCriteriosEvaluacionTestCase(TestCase):
    """HU-42: El evaluador gestiona los ítems de evaluación asociados a un evento"""

    def setUp(self):
        # Crear usuario y administrador
        self.user = User.objects.create_user(username="admin", password="12345")
        self.admin = Administradores.objects.create(usuario=self.user)

        # Crear evento de prueba
        self.evento = Eventos.objects.create(
            eve_nombre="Feria Innovación 2025",
            eve_descripcion="Evento de innovación",
            eve_ciudad="Manizales",
            eve_lugar="Teatro Fundadores",
            eve_fecha_inicio="2025-11-10",
            eve_fecha_fin="2025-11-12",
            eve_estado="Activo",
            eve_imagen="image/test.png",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        self.client = Client()

    # ---------------- CA1 ----------------
    def test_agregar_criterios_exitosamente(self):
        """CA1: El evaluador puede agregar nuevos criterios sin superar el 100%"""
        url = reverse('app_evaluador:crud_criterios_evento', args=[self.evento.id])
        data = {
            'criterio[]': ['Claridad', 'Originalidad'],
            'porcentaje[]': ['40', '60']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Criterios.objects.filter(cri_evento_fk=self.evento).count(), 2)

    # ---------------- CA2 ----------------
    def test_modificar_criterio_exitosamente(self):
        """CA2: El evaluador puede modificar un criterio existente"""
        criterio = Criterios.objects.create(
            cri_descripcion="Presentación",
            cri_peso=Decimal('50.00'),
            cri_evento_fk=self.evento
        )

        url = reverse('administrador:modificar_criterio', args=[criterio.id])
        data = {
            "descripcion": "Presentación final",
            "porcentaje": "60.00"
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        criterio.refresh_from_db()
        self.assertEqual(criterio.cri_descripcion, "Presentación final")
        self.assertEqual(criterio.cri_peso, Decimal('60.00'))
        self.assertJSONEqual(response.content, {'success': True})

    # ---------------- CA3 ----------------
    def test_eliminar_criterio_exitosamente(self):
        """CA3: El evaluador puede eliminar un criterio correctamente"""
        criterio = Criterios.objects.create(
            cri_descripcion="Creatividad",
            cri_peso=Decimal('30.00'),
            cri_evento_fk=self.evento
        )
        url = reverse('administrador:eliminar_criterio', args=[criterio.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Criterios.objects.filter(id=criterio.id).exists())
        self.assertJSONEqual(response.content, {'success': True})
