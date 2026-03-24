from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores

class VerEventoAdmTestCase(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Crear usuario base
        self.user = Usuario.objects.create_user(
            username='superadmin',
            password='testpass123',
            tipo_documento='CC',
            documento_identidad='123456789'
        )
        
        # Crear administrador relacionado
        self.administrador = Administradores.objects.create(
            usuario=self.user,
            num_eventos=5,
            estado='Activo',
            clave_acceso='ABC123'
        )
        
    def crear_evento(self, con_imagen=False, estado='Activo', con_programacion=False):
        """Helper para crear eventos de prueba"""
        evento = Eventos.objects.create(
            eve_nombre='Evento de Prueba',
            eve_descripcion='Descripción detallada del evento de prueba',
            eve_ciudad='Bogotá',
            eve_lugar='Centro de Convenciones',
            eve_fecha_inicio='2024-03-01',
            eve_fecha_fin='2024-03-02',
            eve_estado=estado,
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador,
            eve_habilitar_participantes=True,
            eve_habilitar_evaluadores=True
        )
        
        if con_imagen:
            evento.eve_imagen = SimpleUploadedFile(
                "evento_imagen.jpg", 
                b"fake_image_content", 
                content_type="image/jpeg"
            )
        
        if con_programacion:
            evento.eve_programacion = SimpleUploadedFile(
                "programacion.pdf", 
                b"fake_pdf_content", 
                content_type="application/pdf"
            )
        
        if con_imagen or con_programacion:
            evento.save()
        
        return evento

    def test_usuario_no_autenticado_redirecciona_login(self):
        """CA1: Usuario no autenticado es redirigido al login"""
        evento = self.crear_evento()
        
        # Usar la URL real en lugar de factory directo
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_evento_no_existe_retorna_404(self):
        """CA2: Evento no encontrado retorna 404"""
        self.client.force_login(self.user)
        url = reverse('super_admin:ver_evento_adm', args=[999])  # ID que no existe
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_evento_existe_sin_imagen(self):
        """CA3: Evento sin imagen tiene imagen_url=None"""
        evento = self.crear_evento(con_imagen=False)
        self.client.force_login(self.user)
        
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['evento'].imagen_url)

    def test_evento_carga_relacion_administrador_completa(self):
        """CA1: Verificar que se carga toda la relación con el administrador"""
        evento = self.crear_evento()
        self.client.force_login(self.user)
        
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        evento_context = response.context['evento']
        
        # Verificar relación directa
        self.assertEqual(evento_context.eve_administrador_fk, self.administrador)
        
        # Verificar datos del administrador
        admin = evento_context.eve_administrador_fk
        self.assertEqual(admin.num_eventos, 5)
        self.assertEqual(admin.estado, 'Activo')
        self.assertEqual(admin.clave_acceso, 'ABC123')
        
        # Verificar relación con usuario
        self.assertEqual(admin.usuario, self.user)
        self.assertEqual(admin.usuario.username, 'superadmin')

    def test_evento_con_diferentes_estados(self):
        """CA2: La vista funciona con eventos en diferentes estados"""
        estados = ['Activo', 'Inactivo', 'Finalizado', 'Cancelado']
        
        for estado in estados:
            with self.subTest(estado=estado):
                evento = self.crear_evento(estado=estado)
                self.client.force_login(self.user)
                
                url = reverse('super_admin:ver_evento_adm', args=[evento.id])
                response = self.client.get(url)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['evento'].eve_estado, estado)

    def test_template_correcto_se_utiliza(self):
        """Verificar que se renderiza el template correcto"""
        evento = self.crear_evento()
        self.client.force_login(self.user)
        
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_super_admin/detalle_evento.html')

    def test_contexto_contiene_evento(self):
        """Verificar que el contexto contiene el objeto evento"""
        evento = self.crear_evento()
        self.client.force_login(self.user)
        
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('evento', response.context)
        self.assertEqual(response.context['evento'], evento)

    def test_evento_con_campos_opcionales(self):
        """Test con campos opcionales del modelo Eventos"""
        evento = self.crear_evento(con_programacion=True)
        evento.eve_memorias = 'https://example.com/memorias'
        evento.save()
        
        self.client.force_login(self.user)
        url = reverse('super_admin:ver_evento_adm', args=[evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        evento_context = response.context['evento']
        
        # Verificar campos opcionales
        self.assertIsNotNone(evento_context.eve_programacion)
        self.assertEqual(evento_context.eve_memorias, 'https://example.com/memorias')
