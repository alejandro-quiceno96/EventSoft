from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from app_usuarios.models import Usuario as User
from app_eventos.models import Eventos
from app_certificados.models import Certificado
from app_administrador.models import Administradores
import os

# Constantes simulando los diseños por defecto
DEFAULT_VERTICAL = 'defaults/certificado_vertical.png'
DEFAULT_HORIZONTAL = 'defaults/certificado_defecto.png'

class ConfiguracionCertificadosTestCase(TestCase):

    def setUp(self):
        # Crear usuario administrador
        self.user = User.objects.create_user(username='admin', password='12345')
        self.client = Client()
        self.client.login(username='admin', password='12345')

        # Crear Administrador asociado al usuario
        self.administrador = Administradores.objects.create(usuario=self.user)

        # Crear evento asociado al administrador
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test',
            eve_descripcion='Descripcion',
            eve_ciudad='Ciudad',
            eve_lugar='Lugar',
            eve_fecha_inicio='2025-01-01',
            eve_fecha_fin='2025-01-02',
            eve_estado='Activo',
            eve_imagen='path/to/image.jpg',
            eve_capacidad=100,
            eve_administrador_fk=self.administrador  # usar objeto, no id
        )

        # Archivos simulados
        self.archivo_diseno = SimpleUploadedFile("diseno.pdf", b"contenido diseno")
        self.archivo_firma = SimpleUploadedFile("firma.pdf", b"contenido firma")

    def test_get_formulario_sin_certificado(self):
        """GET → formulario sin certificado previo"""
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['certificado'])
        self.assertFalse(response.context['con_diseno'])
        self.assertFalse(response.context['con_firma'])

    def test_post_crear_certificado_diseno_y_firma(self):
        """POST → crear certificado con diseño y firma"""
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        data = {
            'nombre_certificador': 'Certificador',
            'tipografia': 'Arial',
            'orientacion': 'vertical',
            'lugar_expedicion': 'Ciudad',
            'con_diseno': 'si',
            'con_firma': 'si',
            'firma_nombre': 'Nombre Firma',
            'firma_cargo': 'Cargo Firma'
        }
        files = {
            'diseno': self.archivo_diseno,
            'firma': self.archivo_firma
        }
        response = self.client.post(url, data=data, files=files, follow=True)
        self.assertEqual(response.status_code, 200)
        certificado = Certificado.objects.get(evento_fk=self.evento)
        self.assertEqual(certificado.firma_nombre, 'Nombre Firma')
        self.assertEqual(certificado.firma_cargo, 'Cargo Firma')

    def test_post_certificado_existente_actualiza_diseno_y_firma(self):
        """POST → actualizar certificado existente"""
        certificado = Certificado.objects.create(evento_fk=self.evento)
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        data = {
            'nombre_certificador': 'Nuevo Certificador',
            'tipografia': 'Times',
            'orientacion': 'horizontal',
            'lugar_expedicion': 'Otra Ciudad',
            'con_diseno': 'no',
            'con_firma': 'no'
        }
        response = self.client.post(url, data=data, follow=True)
        certificado.refresh_from_db()
        self.assertFalse(certificado.firma)
        self.assertEqual(certificado.orientacion, 'horizontal')

    def test_post_asigna_diseno_por_defecto(self):
        """POST → si no hay diseño, asigna DEFAULT_VERTICAL / HORIZONTAL"""
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        data = {
            'nombre_certificador': 'Certificador',
            'tipografia': 'Arial',
            'orientacion': 'vertical',
            'lugar_expedicion': 'Ciudad',
            'con_diseno': 'no',
            'con_firma': 'no'
        }
        self.client.post(url, data=data)
        certificado = Certificado.objects.get(evento_fk=self.evento)
        self.assertEqual(certificado.diseño, DEFAULT_VERTICAL)

        # Horizontal
        data['orientacion'] = 'horizontal'
        self.client.post(url, data=data)
        certificado.refresh_from_db()
        self.assertEqual(certificado.diseño, DEFAULT_HORIZONTAL)

    def test_get_guardado_param(self):
        """GET → con ?guardado=1"""
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id]) + '?guardado=1'
        response = self.client.get(url)
        self.assertTrue(response.context['guardado'])

    def test_post_diseno_si_sin_archivo(self):
        """POST → con_diseno=si pero sin archivo → mantiene diseño previo o None"""
        certificado = Certificado.objects.create(evento_fk=self.evento, diseño=self.archivo_diseno)
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        data = {
            'nombre_certificador': 'Certificador',
            'tipografia': 'Arial',
            'orientacion': 'vertical',
            'lugar_expedicion': 'Ciudad',
            'con_diseno': 'si',
            'con_firma': 'no'
        }
        self.client.post(url, data=data)
        certificado.refresh_from_db()
        self.assertIsNotNone(certificado.diseño)  # mantiene el diseño previo

    def test_post_firma_si_sin_archivo(self):
        """POST → con_firma=si pero sin archivo → mantiene firma previa pero actualiza nombre/cargo"""
        certificado = Certificado.objects.create(
            evento_fk=self.evento,
            firma=self.archivo_firma,
            firma_nombre='Anterior',
            firma_cargo='Cargo'
        )
        url = reverse('administrador:configuracion_certificados', args=[self.evento.id])
        data = {
            'nombre_certificador': 'Certificador',
            'tipografia': 'Arial',
            'orientacion': 'vertical',
            'lugar_expedicion': 'Ciudad',
            'con_diseno': 'no',
            'con_firma': 'si',
            'firma_nombre': 'Nuevo Nombre',
            'firma_cargo': 'Nuevo Cargo'
        }
        self.client.post(url, data=data)
        certificado.refresh_from_db()
        self.assertIsNotNone(certificado.firma)
        self.assertEqual(certificado.firma_nombre, 'Nuevo Nombre')
        self.assertEqual(certificado.firma_cargo, 'Nuevo Cargo')
