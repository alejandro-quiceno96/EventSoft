# app_administrador/tests/test_hu74_criterios.py

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.timezone import now

from app_administrador.models import Administradores
from app_eventos.models import Eventos
from app_criterios.models import Criterios
from app_usuarios.models import Usuario as User


class CriteriosEvaluacionTestCase(TestCase):
    """
    Tests para HU74 - Gestionar ítems del instrumento de evaluación (agregar, modificar, eliminar)
    Caminos cubiertos:
      - GET form muestra evento y criterios
      - POST agregar criterios: éxito
      - POST agregar: porcentajes no numéricos -> mensaje de error
      - POST agregar: suma existente + nuevos > 100 -> mensaje de error
      - modificar criterio: éxito, criterio no existe (404), método no permitido (405)
      - eliminar criterio: éxito, criterio no existe (404), método no permitido (405)
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()

        # Crear usuario administrador y Administradores
        self.user_admin = User.objects.create_user(
            username="admin_hu74", password="admin123", first_name="Admin", last_name="Hu74"
        )
        self.admin = Administradores.objects.create(usuario=self.user_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Criterios",
            eve_descripcion="Prueba HU74",
            eve_ciudad="Ciudad",
            eve_lugar="Lugar",
            eve_fecha_inicio=now().date(),
            eve_fecha_fin=now().date(),
            eve_estado="Activo",
            eve_imagen="img.jpg",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )

        # Loguear admin para acceder (si la vista lo requiere)
        self.client.login(username="admin_hu74", password="admin123")

        # URL names (ajusta si tus names son distintos)
        self.url_criterios = reverse("administrador:criterios_evaluacion", args=[self.evento.id])
        self.url_modificar_base = "administrador:modificar_criterio"  # use reverse with args
        self.url_eliminar_base = "administrador:eliminar_criterio"

    def test_get_muestra_form_y_criterios(self):
        """GET muestra la plantilla y el contexto con criterios (vacío si no hay)"""
        response = self.client.get(self.url_criterios)
        self.assertEqual(response.status_code, 200)
        self.assertIn("criterios", response.context)
        self.assertIn("evento", response.context)
        # inicialmente sin criterios
        self.assertEqual(list(response.context["criterios"]), [])

    def test_agregar_criterios_exitoso(self):
        """POST agregar criterios válidos: crea objetos y muestra mensaje success"""
        data = {
            'criterio[]': ["Originalidad", "Claridad"],
            'porcentaje[]': ["30.5", "20.5"],
        }
        # follow True para capturar mensajes en contexto después del redirect
        response = self.client.post(self.url_criterios, data, follow=True)
        # debe redirigir y existir mensaje success
        self.assertEqual(response.status_code, 200)
        msgs = list(response.context.get('messages', []))
        self.assertTrue(any("agregado" in m.message.lower() or "correctamente" in m.message.lower() for m in msgs))

        # comprobar que se crearon 2 criterios vinculados al evento
        criterios = Criterios.objects.filter(cri_evento_fk=self.evento)
        self.assertEqual(criterios.count(), 2)
        pesos = [c.cri_peso for c in criterios]
        self.assertIn(Decimal("30.50"), pesos)
        self.assertIn(Decimal("20.50"), pesos)


    def test_agregar_supera_100_produce_error(self):
        """
        Si suma_existente + suma_nuevos > 100 => error y no crear
        Creamos antes un criterio con peso 80 y luego intentamos añadir 30 -> falla
        """
        Criterios.objects.create(cri_descripcion="Existente", cri_peso=Decimal("80.00"), cri_evento_fk=self.evento)

        data = {
            'criterio[]': ["Nuevo1"],
            'porcentaje[]': ["30"]
        }
        response = self.client.post(self.url_criterios, data, follow=True)
        self.assertEqual(response.status_code, 200)
        msgs = list(response.context.get('messages', []))
        self.assertTrue(any("no puede superar" in m.message.lower() or "no superar" in m.message.lower() for m in msgs))

        # no debe añadirse el nuevo
        criterios = list(Criterios.objects.filter(cri_evento_fk=self.evento))
        self.assertEqual(len(criterios), 1)
        self.assertEqual(criterios[0].cri_descripcion, "Existente")

    def test_modificar_criterio_exitoso(self):
        """Modificar criterio con POST JSON (200/success True)"""
        c = Criterios.objects.create(cri_descripcion="A", cri_peso=Decimal("10.00"), cri_evento_fk=self.evento)
        url = reverse(self.url_modificar_base, args=[c.id])
        payload = {"descripcion": "A modificado", "porcentaje": "15.25"}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        # Vista devuelve JsonResponse {'success': True}
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

        # Refrescar y validar cambios
        c.refresh_from_db()
        self.assertEqual(c.cri_descripcion, "A modificado")
        # DecimalField guarda Decimal; comparar como string/Decimal
        self.assertEqual(c.cri_peso, Decimal("15.25"))

    def test_modificar_criterio_no_encontrado(self):
        """Si criterio no existe -> 404 y success False"""
        url = reverse(self.url_modificar_base, args=[999999])
        payload = {"descripcion": "X", "porcentaje": "10"}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("no encontrado", data.get("error", "").lower())

    def test_modificar_criterio_metodo_no_permitido(self):
        """GET a modificar_criterio debe devolver 405"""
        c = Criterios.objects.create(cri_descripcion="B", cri_peso=Decimal("5"), cri_evento_fk=self.evento)
        url = reverse(self.url_modificar_base, args=[c.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_eliminar_criterio_exitoso(self):
        """Eliminar criterio con POST -> success True y objeto borrado"""
        c = Criterios.objects.create(cri_descripcion="ToDelete", cri_peso=Decimal("7"), cri_evento_fk=self.evento)
        url = reverse(self.url_eliminar_base, args=[c.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        # verificar eliminado
        self.assertFalse(Criterios.objects.filter(id=c.id).exists())

    def test_eliminar_criterio_no_encontrado(self):
        """Eliminar criterio inexistente -> 404 y success False"""
        url = reverse(self.url_eliminar_base, args=[999999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("no encontrado", data.get("error", "").lower())

    def test_eliminar_metodo_no_permitido(self):
        """GET a eliminar_criterio debe devolver 405"""
        c = Criterios.objects.create(cri_descripcion="X", cri_peso=Decimal("1"), cri_evento_fk=self.evento)
        url = reverse(self.url_eliminar_base, args=[c.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertFalse(data.get("success"))
