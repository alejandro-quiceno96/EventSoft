import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from app_eventos.models import Eventos, Proyecto, ParticipantesEventos 
from app_participante.models import Participantes
from app_administrador.models import Administradores

User = get_user_model()

class CancelarInscripcionTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.user_admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.administrador = Administradores.objects.create(
            usuario=self.user_admin,
            estado='Activo'
        )
        
        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre='Evento de Prueba',
            eve_descripcion='Descripción del evento',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio',
            eve_fecha_inicio='2024-01-01',
            eve_fecha_fin='2024-01-02',
            eve_estado='activo',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear participantes
        self.user_participante1 = User.objects.create_user(
            username='participante1',
            email='participante1@example.com',
            password='testpass123'
        )
        
        self.user_participante2 = User.objects.create_user(
            username='participante2',
            email='participante2@example.com',
            password='testpass123'
        )
        
        self.participante1 = Participantes.objects.create(usuario=self.user_participante1)
        self.participante2 = Participantes.objects.create(usuario=self.user_participante2)
        
        # Crear proyecto
        self.proyecto = Proyecto.objects.create(
            pro_nombre='Proyecto de Prueba',
            pro_descripcion='Descripción del proyecto',
            pro_evento_fk=self.evento,
            pro_codigo='PROY001',
            pro_estado='Activo',
            pro_documentos=SimpleUploadedFile("proyecto.pdf", b"proyecto_content")
        )
        
        # Crear archivo simulado
        self.archivo_documento = SimpleUploadedFile(
            "documento.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        # Crear inscripciones - USANDO LOS CAMPOS CORRECTOS DEL MODELO
        self.inscripcion1 = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante1,
            par_eve_evento_fk=self.evento,
            par_eve_documentos=self.archivo_documento,
            par_eve_proyecto=self.proyecto,
            par_eve_fecha_hora='2024-01-01 10:00:00',  # Campo correcto
            par_eve_estado='Inscrito',
            par_eve_clave='CLAVE123',
            par_eve_qr=SimpleUploadedFile("qr1.png", b"qr_content"),
            habilitado=True
        )
        
        self.inscripcion2 = ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante2,
            par_eve_evento_fk=self.evento,
            par_eve_proyecto=self.proyecto,
            par_eve_fecha_hora='2024-01-01 10:00:00',  # Campo correcto
            par_eve_estado='Inscrito',
            par_eve_clave='CLAVE456',
            par_eve_qr=SimpleUploadedFile("qr2.png", b"qr_content"),
            habilitado=True
        )
        
        # URL para los tests - AJUSTA SEGÚN TU URL NAME REAL
        self.url = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, self.participante1.id])
        
        # Autenticar como administrador
        self.client.login(username='admin', password='testpass123')
    
    @patch('app_participante.views.default_storage.delete')  # CORREGIDO: app_participante
    def test_cancelacion_inscripcion_exitosa(self, mock_storage_delete):
        """CA1: Cancelación exitosa con eliminación de archivo"""
        response = self.client.post(self.url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que la inscripción fue eliminada
        self.assertFalse(
            ParticipantesEventos.objects.filter(
                par_eve_evento_fk=self.evento.id,
                par_eve_participante_fk=self.participante1.id
            ).exists()
        )
        
        # Verificar que se intentó eliminar el archivo
        mock_storage_delete.assert_called_once()
    
    @patch('app_participante.views.default_storage.delete')  # CORREGIDO: app_participante
    def test_cancelacion_elimina_proyecto_si_es_ultimo_expositor(self, mock_storage_delete):
        """CA1: Elimina proyecto si era el último expositor"""
        # Primero cancelar la segunda inscripción (deja solo una en el proyecto)
        url_participante2 = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, self.participante2.id])
        response1 = self.client.post(url_participante2)
        self.assertTrue(json.loads(response1.content)['success'])
        
        # Verificar que el proyecto sigue existiendo (aún hay un expositor)
        self.assertTrue(Proyecto.objects.filter(id=self.proyecto.id).exists())
        
        # Ahora cancelar la primera inscripción (debería eliminar el proyecto)
        response2 = self.client.post(self.url)
        self.assertTrue(json.loads(response2.content)['success'])
        
        # Verificar que el proyecto fue eliminado
        self.assertFalse(Proyecto.objects.filter(id=self.proyecto.id).exists())
    
    @patch('app_participante.views.default_storage.delete')  # CORREGIDO: app_participante
    def test_cancelacion_elimina_participante_si_es_unica_inscripcion(self, mock_storage_delete):
        """CA1: Elimina participante si era su única inscripción"""
        response = self.client.post(self.url)
        
        # Verificar que el participante fue eliminado
        self.assertFalse(Participantes.objects.filter(id=self.participante1.id).exists())
    
    @patch('app_participante.views.default_storage.delete')  # CORREGIDO: app_participante
    def test_no_elimina_participante_si_tiene_otras_inscripciones(self, mock_storage_delete):
        """CA1: No elimina participante si tiene otras inscripciones"""
        # Crear otra inscripción para el mismo participante
        otro_evento = Eventos.objects.create(
            eve_nombre='Otro Evento',
            eve_descripcion='Otro evento',
            eve_ciudad='Medellín',
            eve_lugar='Sala',
            eve_fecha_inicio='2024-02-01',
            eve_fecha_fin='2024-02-02',
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante1,
            par_eve_evento_fk=otro_evento,
            par_eve_fecha_hora='2024-01-01 10:00:00',
            par_eve_estado='Inscrito',
            par_eve_clave='CLAVE789',
            par_eve_qr=SimpleUploadedFile("qr3.png", b"qr_content"),
            habilitado=True
        )
        
        response = self.client.post(self.url)
        
        # Verificar que el participante NO fue eliminado
        self.assertTrue(Participantes.objects.filter(id=self.participante1.id).exists())
    
    def test_inscripcion_no_encontrada(self):
        """CA2: Inscripción no encontrada retorna error 404"""
        # Usar un participante que no está inscrito
        user_no_inscrito = User.objects.create_user(
            username='noinscrito',
            email='noinscrito@example.com',
            password='testpass123'
        )
        participante_no_inscrito = Participantes.objects.create(usuario=user_no_inscrito)
        
        url = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, participante_no_inscrito.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'No se encontró la inscripción')
    
    def test_participante_no_existe(self):
        """CA2: Participante que no existe retorna error 404"""
        url = reverse('app_participante:cancelar_inscripcion', args=[self.evento.id, 9999])  # ID que no existe
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'No se encontró la inscripción')
    
    def test_metodo_get_no_permitido(self):
        """CA3: Método GET retorna error 405"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Método no permitido')
    
    def test_metodo_put_no_permitido(self):
        """CA3: Método PUT retorna error 405"""
        response = self.client.put(self.url)
        
        self.assertEqual(response.status_code, 405)
    
    def test_usuario_no_autenticado(self):
        """CA3: Usuario no autenticado es redirigido"""
        client_no_auth = Client()
        response = client_no_auth.post(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    @patch('app_participante.views.default_storage.delete')  # CORREGIDO: app_participante
    def test_error_eliminacion_archivo_no_afecta_proceso(self, mock_storage_delete):
        """CA1: Error al eliminar archivo no detiene el proceso"""
        # Configurar mock para que falle la eliminación del archivo
        mock_storage_delete.side_effect = Exception('Error de almacenamiento')
        
        response = self.client.post(self.url)
        
        # Verificar que a pesar del error, la inscripción se cancela
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que la inscripción fue eliminada
        self.assertFalse(
            ParticipantesEventos.objects.filter(
                par_eve_evento_fk=self.evento.id,
                par_eve_participante_fk=self.participante1.id
            ).exists()
        )

