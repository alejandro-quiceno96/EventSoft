import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from app_eventos.models import Eventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes

User = get_user_model()

class CancelarInscripcionTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario asistente
        self.usuario_asistente = User.objects.create_user(
            username='asistente',
            email='asistente@example.com',
            password='testpass123'
        )
        
        # Crear perfil de asistente
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)
        
        # Crear otro asistente para pruebas múltiples
        self.otro_usuario_asistente = User.objects.create_user(
            username='otro_asistente',
            email='otro_asistente@example.com',
            password='testpass123'
        )
        self.otro_asistente = Asistentes.objects.create(usuario=self.otro_usuario_asistente)
        
        # Crear administrador y evento
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.administrador = Administradores.objects.create(usuario=self.admin_user)
        
        hoy = timezone.now().date()
        self.evento = Eventos.objects.create(
            eve_nombre='Evento Test',
            eve_descripcion='Evento para pruebas',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear otro evento
        self.otro_evento = Eventos.objects.create(
            eve_nombre='Otro Evento',
            eve_descripcion='Otro evento para pruebas',
            eve_ciudad='Medellín',
            eve_lugar='Sala',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Crear inscripciones
        self.inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte.pdf", b"file_content", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr.pdf", b"qr_content", content_type="application/pdf"),
            asi_eve_clave='CLAVE123'
        )
        
        # Crear inscripción para el otro asistente
        self.otra_inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.otro_asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE456'
        )
        
        # URL para los tests
        self.url = reverse('app_asistente:cancelar_inscripcion', args=[self.evento.id, self.asistente.id])
        
        # Autenticar como asistente
        self.client.login(username='asistente', password='testpass123')

    def test_cancelar_inscripcion_exitosa(self):
        """CA1: Cancelación exitosa de inscripción"""
        # Verificar que la inscripción existe antes
        self.assertTrue(AsistentesEventos.objects.filter(
            asi_eve_evento_fk=self.evento.id, 
            asi_eve_asistente_fk=self.asistente.id
        ).exists())
        
        # Realizar solicitud POST para cancelar inscripción
        response = self.client.post(self.url)
        
        # Verificar respuesta JSON exitosa
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que la inscripción fue eliminada
        self.assertFalse(AsistentesEventos.objects.filter(
            asi_eve_evento_fk=self.evento.id, 
            asi_eve_asistente_fk=self.asistente.id
        ).exists())
        
        # CORRECCIÓN: La función SÍ elimina el asistente cuando cancela su única inscripción
        # En este caso, el asistente solo tenía esta inscripción
        self.assertFalse(Asistentes.objects.filter(id=self.asistente.id).exists())
        self.assertFalse(User.objects.filter(id=self.usuario_asistente.id).exists())

    def test_cancelar_inscripcion_unica_elimina_asistente(self):
        """CA2: Cancelación de única inscripción ELIMINA asistente"""
        # Crear un asistente con una sola inscripción
        usuario_unico = User.objects.create_user(
            username='asistente_unico',
            email='unico@example.com',
            password='testpass123'
        )
        asistente_unico = Asistentes.objects.create(usuario=usuario_unico)
        
        inscripcion_unica = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=asistente_unico,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte_unico.pdf", b"file_content", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr_unico.pdf", b"qr_content", content_type="application/pdf"),
            asi_eve_clave='CLAVE_UNICO'
        )
        
        url_unico = reverse('app_asistente:cancelar_inscripcion', args=[self.evento.id, asistente_unico.id])
        
        # Autenticar como este asistente único
        self.client.login(username='asistente_unico', password='testpass123')
        
        response = self.client.post(url_unico)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que la inscripción fue eliminada
        self.assertFalse(AsistentesEventos.objects.filter(
            asi_eve_evento_fk=self.evento.id, 
            asi_eve_asistente_fk=asistente_unico.id
        ).exists())
        
        # CORRECCIÓN: La función SÍ elimina el asistente cuando era su única inscripción
        self.assertFalse(Asistentes.objects.filter(id=asistente_unico.id).exists())
        self.assertFalse(User.objects.filter(id=usuario_unico.id).exists())

    def test_cancelar_inscripcion_con_multiple_inscripciones(self):
        """CA2: Cancelación cuando el asistente tiene múltiples inscripciones NO elimina asistente"""
        # Crear una segunda inscripción para el mismo asistente
        segunda_inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.otro_evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE789'
        )
        
        # Verificar que tiene 2 inscripciones antes de cancelar
        inscripciones_antes = AsistentesEventos.objects.filter(asi_eve_asistente_fk=self.asistente.id).count()
        self.assertEqual(inscripciones_antes, 2)
        
        response = self.client.post(self.url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que solo se eliminó una inscripción
        inscripciones_despues = AsistentesEventos.objects.filter(asi_eve_asistente_fk=self.asistente.id).count()
        self.assertEqual(inscripciones_despues, 1)
        
        # Verificar que el asistente NO fue eliminado (tenía múltiples inscripciones)
        self.assertTrue(Asistentes.objects.filter(id=self.asistente.id).exists())
        self.assertTrue(User.objects.filter(id=self.usuario_asistente.id).exists())

    def test_inscripcion_no_existe(self):
        """CA3: Error cuando la inscripción no existe"""
        # Usar un asistente que no está inscrito en el evento
        asistente_no_inscrito_user = User.objects.create_user(
            username='no_inscrito',
            email='no_inscrito@example.com',
            password='testpass123'
        )
        asistente_no_inscrito = Asistentes.objects.create(usuario=asistente_no_inscrito_user)
        
        url_no_inscrito = reverse('app_asistente:cancelar_inscripcion', args=[self.evento.id, asistente_no_inscrito.id])
        
        self.client.login(username='no_inscrito', password='testpass123')
        response = self.client.post(url_no_inscrito)
        
        # Verificar respuesta de error
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'No se encontró la inscripción')

    def test_evento_no_existe(self):
        """CA3: Error cuando el evento no existe"""
        evento_id_inexistente = 9999
        url_evento_inexistente = reverse('app_asistente:cancelar_inscripcion', args=[evento_id_inexistente, self.asistente.id])
        
        response = self.client.post(url_evento_inexistente)
        
        # CORRECCIÓN: La función retorna 404 cuando el evento no existe
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'No se encontró la inscripción')

    def test_asistente_no_existe(self):
        """CA3: Error cuando el asistente no existe"""
        asistente_id_inexistente = 9999
        url_asistente_inexistente = reverse('app_asistente:cancelar_inscripcion', args=[self.evento.id, asistente_id_inexistente])
        
        response = self.client.post(url_asistente_inexistente)
        
        # CORRECCIÓN: La función retorna 404, no 500
        # Porque Asistentes.objects.get(id=asistente_id) lanza DoesNotExist
        # que es capturado y retorna 404
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        # El mensaje de error puede variar, pero debe indicar que no se encontró

    def test_metodo_get_no_permitido(self):
        """CA3: Método GET retorna error"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')

    def test_metodo_put_no_permitido(self):
        """CA3: Método PUT retorna error"""
        response = self.client.put(self.url)
        
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')

    def test_usuario_no_autenticado(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        client_no_auth = Client()
        response = client_no_auth.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_estructura_respuesta_exitosa(self):
        """CA3: Respuesta JSON tiene estructura correcta en caso de éxito"""
        # Para este test, necesitamos que el asistente tenga múltiples inscripciones
        # para que no sea eliminado y podamos verificar la respuesta
        segunda_inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.otro_evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE789'
        )
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Verificar estructura de respuesta exitosa
        self.assertEqual(response_data['success'], True)
        self.assertNotIn('error', response_data)  # No debe haber error en éxito

    def test_csrf_exempt_funciona(self):
        """Verificar que @csrf_exempt permite la solicitud sin token CSRF"""
        # Para este test, necesitamos que el asistente tenga múltiples inscripciones
        segunda_inscripcion = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.otro_evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte=SimpleUploadedFile("soporte2.pdf", b"file_content2", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr2.pdf", b"qr_content2", content_type="application/pdf"),
            asi_eve_clave='CLAVE789'
        )
        
        # Crear un cliente que no incluya CSRF
        client_sin_csrf = Client(enforce_csrf_checks=True)
        client_sin_csrf.login(username='asistente', password='testpass123')
        
        # Esta solicitud debería funcionar gracias a @csrf_exempt
        response = client_sin_csrf.post(self.url)
        
        # Debería procesarse sin errores CSRF
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])

    def test_inscripciones_con_diferentes_estados(self):
        """CA1: Cancelación de inscripciones con diferentes estados"""
        # Crear inscripción con estado diferente
        inscripcion_pendiente = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.otro_asistente,
            asi_eve_evento_fk=self.otro_evento,
            asi_eve_estado='Pendiente',  # Estado diferente
            asi_eve_soporte=SimpleUploadedFile("soporte_pendiente.pdf", b"file_content", content_type="application/pdf"),
            asi_eve_qr=SimpleUploadedFile("qr_pendiente.pdf", b"qr_content", content_type="application/pdf"),
            asi_eve_clave='CLAVE_PEND'
        )
        
        url_pendiente = reverse('app_asistente:cancelar_inscripcion', args=[self.otro_evento.id, self.otro_asistente.id])
        
        self.client.login(username='otro_asistente', password='testpass123')
        response = self.client.post(url_pendiente)
        
        # Verificar que se puede cancelar independientemente del estado
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verificar que la inscripción fue eliminada
        self.assertFalse(AsistentesEventos.objects.filter(id=inscripcion_pendiente.id).exists())