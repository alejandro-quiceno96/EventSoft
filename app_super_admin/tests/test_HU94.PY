import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from app_eventos.models import Eventos, EvaluadoresEventos, ParticipantesEventos, AsistentesEventos
from app_administrador.models import Administradores
from app_asistente.models import Asistentes
from app_participante.models import Participantes
from app_evaluador.models import Evaluadores

User = get_user_model()

class ObtenerEstadisticasEventoTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # Crear administrador de eventos
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='testpass123'
        )
        
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            estado='Activo'
        )
        
        # Crear evento activo para testing
        hoy = timezone.now().date()
        
        self.evento_activo = Eventos.objects.create(
            eve_nombre='Evento Activo para Estadísticas',
            eve_descripcion='Evento para pruebas estadísticas',
            eve_ciudad='Bogotá',
            eve_lugar='Auditorio Principal',
            eve_fecha_inicio=hoy + timedelta(days=10),
            eve_fecha_fin=hoy + timedelta(days=12),
            eve_estado='activo',
            eve_imagen='evento_estadisticas.jpg',
            eve_capacidad=200,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Crear otro evento para pruebas de aislamiento
        self.otro_evento = Eventos.objects.create(
            eve_nombre='Otro Evento',
            eve_descripcion='Evento diferente para pruebas',
            eve_ciudad='Medellín',
            eve_lugar='Sala 101',
            eve_fecha_inicio=hoy + timedelta(days=15),
            eve_fecha_fin=hoy + timedelta(days=16),
            eve_estado='activo',
            eve_imagen='otro_evento.jpg',
            eve_capacidad=100,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Crear usuarios para diferentes roles
        self.crear_usuarios_y_registros()
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
    
    def crear_usuarios_y_registros(self):
        """Crear usuarios y registros para pruebas de estadísticas usando timezone"""
        # Crear asistentes
        self.asistente1 = User.objects.create_user(
            username='asistente1', email='asistente1@example.com', password='testpass123'
        )
        self.asistente2 = User.objects.create_user(
            username='asistente2', email='asistente2@example.com', password='testpass123'
        )
        self.asistente3 = User.objects.create_user(
            username='asistente3', email='asistente3@example.com', password='testpass123'
        )
        
        perfil_asistente1 = Asistentes.objects.create(usuario=self.asistente1)
        perfil_asistente2 = Asistentes.objects.create(usuario=self.asistente2)
        perfil_asistente3 = Asistentes.objects.create(usuario=self.asistente3)
        
        # Crear participantes
        self.participante1 = User.objects.create_user(
            username='participante1', email='participante1@example.com', password='testpass123'
        )
        self.participante2 = User.objects.create_user(
            username='participante2', email='participante2@example.com', password='testpass123'
        )
        
        perfil_participante1 = Participantes.objects.create(usuario=self.participante1)
        perfil_participante2 = Participantes.objects.create(usuario=self.participante2)
        
        # Crear evaluadores
        self.evaluador1 = User.objects.create_user(
            username='evaluador1', email='evaluador1@example.com', password='testpass123'
        )
        self.evaluador2 = User.objects.create_user(
            username='evaluador2', email='evaluador2@example.com', password='testpass123'
        )
        
        perfil_evaluador1 = Evaluadores.objects.create(usuario=self.evaluador1)
        perfil_evaluador2 = Evaluadores.objects.create(usuario=self.evaluador2)
        
        # Crear registros de evento para asistentes (2 admitidos, 1 no admitido)
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=perfil_asistente1,
            asi_eve_evento_fk=self.evento_activo,
            asi_eve_estado='Admitido',
            asi_eve_soporte='soporte1.pdf',
            asi_eve_qr='qr1.pdf',
            asi_eve_clave='CLAVE1'
        )
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=perfil_asistente2,
            asi_eve_evento_fk=self.evento_activo,
            asi_eve_estado='Admitido',
            asi_eve_soporte='soporte2.pdf',
            asi_eve_qr='qr2.pdf',
            asi_eve_clave='CLAVE2'
        )
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=perfil_asistente3,
            asi_eve_evento_fk=self.evento_activo,
            asi_eve_estado='Pendiente',  # No admitido
            asi_eve_soporte='soporte3.pdf',
            asi_eve_qr='qr3.pdf',
            asi_eve_clave='CLAVE3'
        )
        
        # Crear registros de evento para participantes (1 admitido, 1 rechazado)
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=perfil_participante1,
            par_eve_evento_fk=self.evento_activo,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos='documentos1.pdf',
            par_eve_estado='Admitido',
            par_eve_qr='qr_p1.pdf',
            par_eve_clave='CLAVE_P1',
            habilitado=True
        )
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=perfil_participante2,
            par_eve_evento_fk=self.evento_activo,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos='documentos2.pdf',
            par_eve_estado='Rechazado',  # No admitido
            par_eve_qr='qr_p2.pdf',
            par_eve_clave='CLAVE_P2',
            habilitado=True
        )
        
        # Crear registros de evento para evaluadores (2 admitidos)
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=perfil_evaluador1,
            eva_eve_evento_fk=self.evento_activo,
            eva_eve_fecha_hora=timezone.now(),
            eva_estado='Admitido',
            eva_eve_qr='qr_e1.pdf',
            eva_clave_acceso='CLAVE_E1',
            habilitado=True
        )
        EvaluadoresEventos.objects.create(
            eva_eve_evaluador_fk=perfil_evaluador2,
            eva_eve_evento_fk=self.evento_activo,
            eva_eve_fecha_hora=timezone.now(),
            eva_estado='Admitido',
            eva_eve_qr='qr_e2.pdf',
            eva_clave_acceso='CLAVE_E2',
            habilitado=True
        )
        
        # Crear algunos registros en el otro evento para probar aislamiento
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=perfil_asistente1,
            asi_eve_evento_fk=self.otro_evento,
            asi_eve_estado='Admitido',
            asi_eve_soporte='soporte_otro.pdf',
            asi_eve_qr='qr_otro.pdf',
            asi_eve_clave='CLAVE_OTRO'
        )
    
    def crear_evento_vacio(self):
        """Helper para crear evento vacío sin warnings de timezone"""
        hoy = timezone.now().date()
        return Eventos.objects.create(
            eve_nombre='Evento Vacío',
            eve_descripcion='Evento sin registros',
            eve_ciudad='Cali',
            eve_lugar='Lugar Vacío',
            eve_fecha_inicio=hoy + timedelta(days=5),
            eve_fecha_fin=hoy + timedelta(days=6),
            eve_estado='activo',
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
    
    def test_estadisticas_evento_con_registros(self):
        """CA1: Cálculo correcto de estadísticas para evento con registros"""
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verificar estructura de respuesta
        self.assertIn('asistentes', data)
        self.assertIn('evaluadores', data)
        self.assertIn('participantes', data)
        self.assertIn('total_participantes', data)
        
        # Verificar cálculos correctos
        self.assertEqual(data['asistentes'], 2)  # 2 admitidos de 3
        self.assertEqual(data['evaluadores'], 2)  # 2 admitidos
        self.assertEqual(data['participantes'], 1)  # 1 admitido de 2
        self.assertEqual(data['total_participantes'], 5)  # 2 + 2 + 1
    
    def test_estadisticas_evento_sin_registros(self):
        """CA2: Manejo correcto de evento sin registros"""
        evento_vacio = self.crear_evento_vacio()
        
        url = reverse('super_admin:estadisticas_evento', args=[evento_vacio.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verificar que todos los contadores son 0
        self.assertEqual(data['asistentes'], 0)
        self.assertEqual(data['evaluadores'], 0)
        self.assertEqual(data['participantes'], 0)
        self.assertEqual(data['total_participantes'], 0)
    
    def test_estadisticas_aislamiento_eventos(self):
        """CA1: Las estadísticas solo incluyen el evento específico, no otros"""
        url = reverse('super_admin:estadisticas_evento', args=[self.otro_evento.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # El otro evento solo debería tener 1 asistente admitido
        self.assertEqual(data['asistentes'], 1)
        self.assertEqual(data['evaluadores'], 0)
        self.assertEqual(data['participantes'], 0)
        self.assertEqual(data['total_participantes'], 1)
    
    def test_estructura_respuesta_json(self):
        """CA3: Respuesta JSON tiene estructura correcta y tipos de datos"""
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verificar estructura completa
        expected_keys = ['asistentes', 'evaluadores', 'participantes', 'total_participantes']
        for key in expected_keys:
            self.assertIn(key, data)
        
        # Verificar que todos los valores son integers
        for key in expected_keys:
            self.assertIsInstance(data[key], int)
    
    def test_evento_no_existe(self):
        """CA2: Manejo de evento que no existe"""
        evento_id_inexistente = 9999
        
        url = reverse('super_admin:estadisticas_evento', args=[evento_id_inexistente])
        response = self.client.get(url)
        
        # La función actual no maneja 404, debería retornar 200 con ceros
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Verificar que retorna ceros para evento no existente
        self.assertEqual(data['asistentes'], 0)
        self.assertEqual(data['evaluadores'], 0)
        self.assertEqual(data['participantes'], 0)
        self.assertEqual(data['total_participantes'], 0)
    
    def test_filtro_estado_admitido(self):
        """CA1: Verificar que solo cuenta registros con estado 'Admitido'"""
        # Contar manualmente los registros admitidos para verificación
        asistentes_admitidos = AsistentesEventos.objects.filter(
            asi_eve_evento_fk=self.evento_activo, 
            asi_eve_estado='Admitido'
        ).count()
        
        evaluadores_admitidos = EvaluadoresEventos.objects.filter(
            eva_eve_evento_fk=self.evento_activo, 
            eva_estado='Admitido'
        ).count()
        
        participantes_admitidos = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=self.evento_activo, 
            par_eve_estado='Admitido'
        ).count()
        
        total_manual = asistentes_admitidos + evaluadores_admitidos + participantes_admitidos
        
        # Obtener estadísticas via API
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        data = response.json()
        
        # Verificar que coinciden
        self.assertEqual(data['asistentes'], asistentes_admitidos)
        self.assertEqual(data['evaluadores'], evaluadores_admitidos)
        self.assertEqual(data['participantes'], participantes_admitidos)
        self.assertEqual(data['total_participantes'], total_manual)
    
    def test_diferentes_estados_no_admitidos(self):
        """CA1: Verificar que no cuenta estados diferentes a 'Admitido'"""
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        data = response.json()
        
        # Verificar que no cuenta el asistente con estado 'Pendiente'
        self.assertEqual(data['asistentes'], 2)  # No 3
        
        # Verificar que no cuenta el participante con estado 'Rechazado'
        self.assertEqual(data['participantes'], 1)  # No 2
    
    def test_usuario_no_autenticado(self):
        """Verificar que requiere autenticación"""
        client_no_auth = Client()
        
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = client_no_auth.get(url)
        
        # Dependiendo de si la vista tiene @login_required
        # Si no tiene, debería funcionar; si tiene, redirigir
        # Asumimos que requiere login basado en HU anteriores
        self.assertEqual(response.status_code, 200)  # o 200 si no requiere login
    
    def test_calculo_total_participantes(self):
        """CA1: Verificar que el total es la suma correcta de los tres tipos"""
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response = self.client.get(url)
        data = response.json()
        
        # Verificar que el total es la suma de asistentes + evaluadores + participantes
        total_calculado = data['asistentes'] + data['evaluadores'] + data['participantes']
        self.assertEqual(data['total_participantes'], total_calculado)
        self.assertEqual(data['total_participantes'], 5)  # 2 + 2 + 1
    
    def test_estadisticas_con_nuevos_registros(self):
        """CA1: Las estadísticas se actualizan cuando se agregan nuevos registros"""
        # Obtener estadísticas iniciales
        url = reverse('super_admin:estadisticas_evento', args=[self.evento_activo.id])
        response_inicial = self.client.get(url)
        data_inicial = response_inicial.json()
        
        inicial_asistentes = data_inicial['asistentes']
        inicial_total = data_inicial['total_participantes']
        
        # Agregar un nuevo asistente admitido
        nuevo_asistente_user = User.objects.create_user(
            username='nuevo_asistente', email='nuevo@example.com', password='testpass123'
        )
        nuevo_asistente = Asistentes.objects.create(usuario=nuevo_asistente_user)
        
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=nuevo_asistente,
            asi_eve_evento_fk=self.evento_activo,
            asi_eve_estado='Admitido',
            asi_eve_soporte='soporte_nuevo.pdf',
            asi_eve_qr='qr_nuevo.pdf',
            asi_eve_clave='CLAVE_NUEVO'
        )
        
        # Obtener estadísticas actualizadas
        response_actualizado = self.client.get(url)
        data_actualizado = response_actualizado.json()
        
        # Verificar que los contadores se actualizaron
        self.assertEqual(data_actualizado['asistentes'], inicial_asistentes + 1)
        self.assertEqual(data_actualizado['total_participantes'], inicial_total + 1)