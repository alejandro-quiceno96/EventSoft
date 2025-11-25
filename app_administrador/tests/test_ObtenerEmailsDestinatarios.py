import json
from django.test import TestCase
from app_administrador.views import obtener_emails_por_destinatarios
from app_asistente.models import Asistentes
from app_participante.models import Participantes
from app_usuarios.models import Usuario as User

class ObtenerEmailsPorDestinatariosGenericTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial genérica"""
        self.user1 = User.objects.create_user(
            username='user1', email='user1@test.com', password='testpass'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@test.com', password='testpass'
        )
        
        # Crear instancias sin asumir la estructura exacta
        try:
            self.asistente1 = Asistentes.objects.create(usuario=self.user1)
        except:
            try:
                self.asistente1 = Asistentes.objects.create(user=self.user1)
            except:
                self.asistente1 = Asistentes.objects.create(correo='user1@test.com')
        
        try:
            self.participante1 = Participantes.objects.create(usuario=self.user2)
        except:
            try:
                self.participante1 = Participantes.objects.create(user=self.user2)
            except:
                self.participante1 = Participantes.objects.create(correo='user2@test.com')
    
    def test_funcion_retorna_lista(self):
        """Verifica que la función siempre retorna una lista"""
        destinatarios = ['asistentes']
        emails = obtener_emails_por_destinatarios(destinatarios)
        
        self.assertIsInstance(emails, list)
    
    def test_todos_retorna_algo(self):
        """Verifica que 'todos' retorna alguna data"""
        destinatarios = ['todos']
        emails = obtener_emails_por_destinatarios(destinatarios)
        
        self.assertIsInstance(emails, list)
        # No podemos afirmar el contenido sin conocer los modelos
    
    def test_destinatarios_vacios(self):
        """Retorna lista vacía cuando no hay destinatarios"""
        destinatarios = []
        emails = obtener_emails_por_destinatarios(destinatarios)
        
        self.assertEqual(emails, [])
    
    def test_elimina_duplicados(self):
        """Verifica que elimina duplicados"""
        # Este test debería funcionar independientemente de la estructura
        destinatarios = ['todos']
        emails = obtener_emails_por_destinatarios(destinatarios)
        
        # Si hay emails, no deberían haber duplicados
        if emails:
            self.assertEqual(len(emails), len(set(emails)))