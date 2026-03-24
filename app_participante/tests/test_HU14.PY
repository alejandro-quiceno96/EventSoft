from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from app_eventos.models import Eventos, ParticipantesEventos, Proyecto
from app_administrador.models import Administradores
from app_participante.models import Participantes

User = get_user_model()

# Configuración temporal para archivos
@override_settings(MEDIA_ROOT='/tmp/django_test')
class TestFlujoCompletoPreinscripcion(TestCase):
    """
    Tests para el flujo COMPLETO de preinscripción
    Incluye ambas funciones y sus interacciones
    """
    
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='1234567890'
        )
        
        # Crear participante (se crea automáticamente en la función)
        self.participante = Participantes.objects.create(usuario=self.user)
        
        # Crear administrador
        self.admin = Administradores.objects.create(usuario=self.user)
        
        # Fecha futura
        self.futuro = timezone.now().date().replace(year=timezone.now().year + 1)
        
        # Crear evento SIN costo (para post_asistente.html)
        self.evento_gratis = Eventos.objects.create(
            eve_nombre='Evento Gratuito',
            eve_descripcion='Test',
            eve_ciudad='Bogotá',
            eve_lugar='Test',
            eve_fecha_inicio=self.futuro,
            eve_fecha_fin=self.futuro,
            eve_estado='Activo',
            eve_imagen='image/test.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        # Crear evento CON costo
        self.evento_pago = Eventos.objects.create(
            eve_nombre='Evento de Pago',
            eve_descripcion='Test',
            eve_ciudad='Medellín',
            eve_lugar='Test',
            eve_fecha_inicio=self.futuro,
            eve_fecha_fin=self.futuro,
            eve_estado='Activo',
            eve_imagen='image/test2.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,
            eve_administrador_fk=self.admin
        )
        
        # Crear proyecto existente para asociar
        self.proyecto_existente = Proyecto.objects.create(
            pro_evento_fk=self.evento_gratis,
            pro_codigo='ABC123',
            pro_nombre='Proyecto Existente',
            pro_descripcion='Descripción proyecto existente',
            pro_documentos='pdf/proyectos/existente.pdf',
            pro_estado='Pendiente'
        )
        
        # Archivo simulado para pruebas
        self.archivo_simulado = SimpleUploadedFile(
            "documento.pdf",
            b"contenido del pdf",
            content_type="application/pdf"
        )
        
        self.client = Client()
        
    # ========== FUNCIÓN 1: preinscripcion_asistente ==========
    
    def test_preinscripcion_evento_gratuito_redirige_a_post(self):
        """Evento sin costo muestra post_asistente.html"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('preinscripcion_asistente', args=[self.evento_gratis.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/post_asistente.html')
        self.assertIn('evento_id', response.context)
        
    def test_preinscripcion_evento_pago_muestra_registro(self):
        """Evento con costo muestra registro_asistente.html"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('preinscripcion_asistente', args=[self.evento_pago.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_visitante/registro_asistente.html')
        self.assertIn('evento', response.context)
        
    # ========== FUNCIÓN 2: submit_preinscripcion_participante ==========
    
    def test_submit_metodo_no_post_redirige(self):
        """Método GET redirige a inicio_visitante"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('inicio_visitante'))
        
    def test_submit_sin_evento_id_404(self):
        """POST sin evento_id causa 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'opcion': 'inscribir',
            'pro_nombre': 'Proyecto Test',
            'pro_descripcion': 'Descripción test'
        })
        
        self.assertEqual(response.status_code, 404)
        
    def test_submit_sin_opcion_invalida(self):
        """POST sin opción válida redirige con error"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'opcion_invalida'  # No es "inscribir" ni "asociar"
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('error=opcion_invalida', response.url)
        
    def test_submit_inscribir_sin_documentos_redirige(self):
        """Inscribir sin documentos redirige a detalle_evento"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'inscribir',
            'pro_nombre': 'Proyecto Test',
            'pro_descripcion': 'Descripción test'
            # Sin pro_documentos
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('detalle_evento', args=[self.evento_gratis.id])
        )
        
    def test_submit_inscribir_con_documentos_exitoso(self):
        """Inscribir con documentos crea proyecto e inscripción"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        
        # Contar registros antes
        proyectos_antes = Proyecto.objects.count()
        inscripciones_antes = ParticipantesEventos.objects.count()
        
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'inscribir',
            'pro_nombre': 'Nuevo Proyecto',
            'pro_descripcion': 'Descripción nuevo proyecto',
            'pro_documentos': self.archivo_simulado
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('registro=exito_participante', response.url)
        
        # Verificar creación de registros
        self.assertEqual(Proyecto.objects.count(), proyectos_antes + 1)
        self.assertEqual(ParticipantesEventos.objects.count(), inscripciones_antes + 1)
        
        # Verificar datos del proyecto creado
        proyecto_creado = Proyecto.objects.last()
        self.assertEqual(proyecto_creado.pro_nombre, 'Nuevo Proyecto')
        self.assertEqual(proyecto_creado.pro_evento_fk, self.evento_gratis)
        self.assertEqual(proyecto_creado.pro_estado, 'Pendiente')
        self.assertIsNotNone(proyecto_creado.pro_codigo)  # generado por función
        
        # Verificar inscripción
        inscripcion = ParticipantesEventos.objects.last()
        self.assertEqual(inscripcion.par_eve_participante_fk, self.participante)
        self.assertEqual(inscripcion.par_eve_evento_fk, self.evento_gratis)
        self.assertEqual(inscripcion.par_eve_proyecto, proyecto_creado)
        self.assertEqual(inscripcion.par_eve_estado, 'Pendiente')
        
    def test_submit_asociar_proyecto_no_valido(self):
        """Asociar proyecto de otro evento redirige con error"""
        self.client.login(username='testuser', password='testpass123')
        
        # Crear proyecto de OTRO evento
        otro_evento = Eventos.objects.create(
            eve_nombre='Otro Evento',
            eve_descripcion='Test',
            eve_ciudad='Cali',
            eve_lugar='Test',
            eve_fecha_inicio=self.futuro,
            eve_fecha_fin=self.futuro,
            eve_estado='Activo',
            eve_imagen='image/otro.jpg',
            eve_capacidad=10,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        proyecto_otro_evento = Proyecto.objects.create(
            pro_evento_fk=otro_evento,  # DIFERENTE evento
            pro_codigo='XYZ789',
            pro_nombre='Proyecto Otro Evento',
            pro_descripcion='Descripción',
            pro_documentos='pdf/proyectos/otro.pdf',
            pro_estado='Pendiente'
        )
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'asociar',
            'proyecto_id': proyecto_otro_evento.id
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('error=proyecto_no_valido', response.url)
        
    def test_submit_asociar_ya_inscrito(self):
        """Asociar cuando ya está inscrito redirige con error"""
        self.client.login(username='testuser', password='testpass123')
        
        # Crear inscripción previa
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=self.participante,
            par_eve_evento_fk=self.evento_gratis,
            par_eve_fecha_hora=timezone.now(),
            par_eve_estado='Pendiente',
            par_eve_qr='',
            par_eve_clave='',
            par_eve_proyecto=self.proyecto_existente
        )
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'asociar',
            'proyecto_id': self.proyecto_existente.id
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('error=ya_inscrito', response.url)
        
    def test_submit_asociar_exitoso(self):
        """Asociar proyecto existente exitosamente"""
        self.client.login(username='testuser', password='testpass123')
        
        # Contar inscripciones antes
        inscripciones_antes = ParticipantesEventos.objects.count()
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'asociar',
            'proyecto_id': self.proyecto_existente.id
        })
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertIn('registro=exito_participante', response.url)
        
        # Verificar creación de inscripción
        self.assertEqual(ParticipantesEventos.objects.count(), inscripciones_antes + 1)
        
        # Verificar datos de la inscripción
        inscripcion = ParticipantesEventos.objects.last()
        self.assertEqual(inscripcion.par_eve_participante_fk, self.participante)
        self.assertEqual(inscripcion.par_eve_evento_fk, self.evento_gratis)
        self.assertEqual(inscripcion.par_eve_proyecto, self.proyecto_existente)
        
    # ========== CAMINOS DE INTEGRACIÓN ==========
    
    def test_flujo_completo_gratuito_post_automatico(self):
        """Flujo completo: evento gratis -> post_asistente -> inscripción"""
        # 1. Login
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Acceder a preinscripción (debería mostrar post_asistente)
        url_preinscripcion = reverse('preinscripcion_asistente', args=[self.evento_gratis.id])
        response1 = self.client.get(url_preinscripcion)
        
        self.assertTemplateUsed(response1, 'app_visitante/post_asistente.html')
        self.assertIn('evento_id', response1.context)
        
        # 3. Simular el POST automático que haría post_asistente.html
        # (Normalmente esto lo haría JavaScript en la plantilla)
        url_submit = reverse('submit_preinscripcion_participante')
        
        # Contar registros antes
        proyectos_antes = Proyecto.objects.count()
        
        response2 = self.client.post(url_submit, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'inscribir',
            'pro_nombre': 'Proyecto desde Flujo',
            'pro_descripcion': 'Descripción desde flujo completo',
            'pro_documentos': self.archivo_simulado
        })
        
        # Verificar éxito
        self.assertEqual(response2.status_code, 302)
        self.assertIn('registro=exito_participante', response2.url)
        
        # Verificar creación
        self.assertEqual(Proyecto.objects.count(), proyectos_antes + 1)
        
    def test_participante_creado_automaticamente(self):
        """Participante se crea automáticamente si no existe"""
        # Crear nuevo usuario SIN participante
        nuevo_user = User.objects.create_user(
            username='nuevouser',
            password='testpass',
            tipo_documento='TI',
            documento_identidad='987654321'
        )
        
        self.client.login(username='nuevouser', password='testpass')
        
        # Verificar que no existe participante
        self.assertFalse(Participantes.objects.filter(usuario=nuevo_user).exists())
        
        # Hacer submit
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'inscribir',
            'pro_nombre': 'Proyecto Auto',
            'pro_descripcion': 'Descripción',
            'pro_documentos': self.archivo_simulado
        })
        
        # Verificar que se creó el participante
        self.assertTrue(Participantes.objects.filter(usuario=nuevo_user).exists())
        
        # Verificar éxito en inscripción
        self.assertEqual(response.status_code, 302)
        self.assertIn('registro=exito_participante', response.url)
        
    # ========== CASOS BORDE Y ERRORES ==========
    
    def test_evento_inexistente_en_submit(self):
        """Evento_id que no existe en submit causa 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': 99999,  # No existe
            'opcion': 'inscribir'
        })
        
        self.assertEqual(response.status_code, 404)
        
    def test_proyecto_inexistente_en_asociar(self):
        """proyecto_id que no existe en asociar causa 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'asociar',
            'proyecto_id': 99999  # No existe
        })
        
        self.assertEqual(response.status_code, 404)
        
    def test_campos_vacios_en_inscribir(self):
        """Campos vacíos en inscribir (excepto documentos) se permiten"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('submit_preinscripcion_participante')
        
        response = self.client.post(url, {
            'evento_id': self.evento_gratis.id,
            'opcion': 'inscribir',
            'pro_nombre': '',  # Vacío
            'pro_descripcion': '',  # Vacío
            'pro_documentos': self.archivo_simulado
        })
        
        # Se crea igual (depende de validaciones del modelo)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó el proyecto (aunque con campos vacíos)
        proyecto = Proyecto.objects.last()
        self.assertEqual(proyecto.pro_nombre, '')
        self.assertEqual(proyecto.pro_descripcion, '')
        