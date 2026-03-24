from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app_eventos.models import Eventos
from app_administrador.models import Administradores

User = get_user_model()

class TestPreinscripcionAsistenteExacta(TestCase):
    """
    Tests para la función EXACTA proporcionada
    Sin modificaciones, sin validaciones adicionales
    """
    
    def setUp(self):
        # Usuario para autenticación
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='1234567890'
        )
        
        # Administrador
        self.admin = Administradores.objects.create(
            usuario=self.user
        )
        
        # Evento SIN costo (False)
        self.evento_gratis = Eventos.objects.create(
            eve_nombre='Evento Gratuito',
            eve_descripcion='Test',
            eve_ciudad='Bogotá',
            eve_lugar='Test',
            eve_fecha_inicio='2024-12-01',
            eve_fecha_fin='2024-12-02',
            eve_estado='Activo',
            eve_imagen='image/test.jpg',
            eve_capacidad=100,
            eve_tienecosto=False,  # EXPLÍCITAMENTE False
            eve_administrador_fk=self.admin
        )
        
        # Evento CON costo (True)
        self.evento_pago = Eventos.objects.create(
            eve_nombre='Evento de Pago',
            eve_descripcion='Test',
            eve_ciudad='Medellín',
            eve_lugar='Test',
            eve_fecha_inicio='2024-12-01',
            eve_fecha_fin='2024-12-02',
            eve_estado='Activo',
            eve_imagen='image/test2.jpg',
            eve_capacidad=50,
            eve_tienecosto=True,  # EXPLÍCITAMENTE True
            eve_administrador_fk=self.admin
        )
        
        self.client = Client()
    
    # ========== CAMINO A: Usuario NO autenticado ==========
    def test_camino_a_usuario_no_autenticado(self):
        """Decorador redirige a login cuando usuario no está autenticado"""
        # NOTA: Reemplaza 'nombre_url_real' con el name real de tu URL
        url = reverse('preinscripcion_asistente', args=[self.evento_gratis.id])
        response = self.client.get(url)
        
        # Verificar redirección (302)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que redirige a login
        # Django puede agregar parámetros como ?next=...
        self.assertIn('/login', response.url)
    
    # ========== CAMINO B: Evento NO existe ==========
    def test_camino_b_evento_no_existe(self):
        """Evento inexistente retorna 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('preinscripcion_asistente', args=[99999])  # ID inexistente
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    # ========== CAMINO C: Evento con eve_tienecosto = False ==========
    def test_camino_c_evento_gratuito_false(self):
        """Evento con eve_tienecosto=False -> post_asistente.html"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('preinscripcion_asistente', args=[self.evento_gratis.id])
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar plantilla correcta
        self.assertTemplateUsed(response, 'app_visitante/post_asistente.html')
        
        # Verificar contexto CORRECTO: solo evento_id
        self.assertIn('evento_id', response.context)
        self.assertEqual(response.context['evento_id'], self.evento_gratis.id)
        
        # Verificar que NO se pasa el objeto evento
        self.assertNotIn('evento', response.context)
        
        # Verificar valor booleano
        self.assertFalse(self.evento_gratis.eve_tienecosto)
    
    # ========== CAMINO D: Evento con eve_tienecosto = True ==========
    def test_camino_d_evento_pago_true(self):
        """Evento con eve_tienecosto=True -> registro_asistente.html"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('preinscripcion_asistente', args=[self.evento_pago.id])
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar plantilla correcta
        self.assertTemplateUsed(response, 'app_visitante/registro_asistente.html')
        
        # Verificar contexto CORRECTO: objeto evento completo
        self.assertIn('evento', response.context)
        self.assertEqual(response.context['evento'], self.evento_pago)
        
        # Verificar que NO se pasa solo el ID
        self.assertNotIn('evento_id', response.context)
        
        # Verificar valor booleano
        self.assertTrue(self.evento_pago.eve_tienecosto)