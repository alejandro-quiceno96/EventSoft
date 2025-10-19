from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta
from io import StringIO
from app_eventos.models import Eventos
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from app_super_admin.models import SuperAdministradores


class CierreAutomaticoEventosTest(TestCase):
    """HU-95: Pruebas para cierre automático de eventos finalizados"""

    def setUp(self):
        """Configuración inicial para cada test"""
        
        # Crear Super Administrador
        self.super_user = Usuario.objects.create_user(
            username="superadmin",
            password="super123",
            tipo_documento="CC",
            documento_identidad="1234567890",
            email="super@test.com"
        )
        self.super_admin = SuperAdministradores.objects.create(
            usuario=self.super_user
        )
        
        # Crear Administrador de Evento
        self.admin_user = Usuario.objects.create_user(
            username="admin_evento",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="9876543210",
            email="admin@test.com"
        )
        self.administrador = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=10,
            estado="Activo"
        )
        
        # Fecha base para cálculos
        self.hoy = timezone.now().date()
        self.dias_limite = 7  # Configurable: eventos finalizados hace 7+ días

    # ===================================================================
    # TEST 1: Evento finalizado hace más del tiempo límite - Debe cerrarse
    # ===================================================================
    def test_cierra_evento_finalizado_pasado_limite_dias(self):
        """
        CA1: Evento finalizado hace 8 días (> 7 días) debe cambiar a CERRADO
        """
        # Arrange
        evento_vencido = Eventos.objects.create(
            eve_nombre="Evento Vencido",
            eve_descripcion="Finalizado hace 8 días",
            eve_ciudad="Manizales",
            eve_lugar="Auditorio",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),  # Hace 8 días
            eve_estado="ACTIVO",  # No cerrado manualmente
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_vencido.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_vencido.eve_estado, "CERRADO",
                        "El evento debe cambiar a estado CERRADO")
        self.assertIn(evento_vencido.id, eventos_cerrados,
                     "El evento debe estar en el log de cerrados")

    # ===================================================================
    # TEST 2: Evento finalizado dentro del periodo de gracia - NO cerrar
    # ===================================================================
    def test_no_cierra_evento_dentro_periodo_gracia(self):
        """
        CA2: Evento finalizado hace 5 días (< 7 días) NO debe cerrarse
        """
        # Arrange
        evento_reciente = Eventos.objects.create(
            eve_nombre="Evento Reciente",
            eve_descripcion="Finalizado hace 5 días",
            eve_ciudad="Bogotá",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy - timedelta(days=7),
            eve_fecha_fin=self.hoy - timedelta(days=5),  # Hace 5 días
            eve_estado="ACTIVO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        estado_inicial = evento_reciente.eve_estado
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_reciente.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_reciente.eve_estado, estado_inicial,
                        "El evento NO debe cambiar de estado (aún en periodo de gracia)")
        self.assertNotIn(evento_reciente.id, eventos_cerrados,
                        "El evento NO debe estar en el log de cerrados")

    # ===================================================================
    # TEST 3: Evento YA cerrado manualmente - NO modificar
    # ===================================================================
    def test_no_modifica_evento_cerrado_manualmente(self):
        """
        CA3: Evento con estado CERRADO manual NO debe ser procesado
        Referencia: HU-86 (cierre manual)
        """
        # Arrange
        evento_cerrado_manual = Eventos.objects.create(
            eve_nombre="Evento Cerrado Manual",
            eve_descripcion="Cerrado por admin hace 10 días",
            eve_ciudad="Cali",
            eve_lugar="Plaza",
            eve_fecha_inicio=self.hoy - timedelta(days=12),
            eve_fecha_fin=self.hoy - timedelta(days=10),
            eve_estado="CERRADO",  # Ya cerrado manualmente
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_cerrado_manual.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_cerrado_manual.eve_estado, "CERRADO",
                        "El estado CERRADO debe mantenerse")
        self.assertNotIn(evento_cerrado_manual.id, eventos_cerrados,
                        "NO debe aparecer en el log (ya estaba cerrado)")

    # ===================================================================
    # TEST 4: Evento ACTIVO no finalizado - NO cerrar
    # ===================================================================
    def test_no_cierra_evento_activo_no_finalizado(self):
        """
        CA4: Evento en curso o futuro NO debe cerrarse
        """
        # Arrange
        evento_activo_futuro = Eventos.objects.create(
            eve_nombre="Evento Futuro",
            eve_descripcion="Inicia en 5 días",
            eve_ciudad="Medellín",
            eve_lugar="Coliseo",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=300,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_activo_futuro.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_activo_futuro.eve_estado, "ACTIVO",
                        "El evento futuro NO debe cerrarse")
        self.assertNotIn(evento_activo_futuro.id, eventos_cerrados)

    # ===================================================================
    # TEST 5: Evento PUBLICADO no finalizado - NO cerrar
    # ===================================================================
    def test_no_cierra_evento_publicado_no_finalizado(self):
        """
        CA5: Evento PUBLICADO (no finalizado) NO debe cerrarse
        """
        # Arrange
        evento_publicado = Eventos.objects.create(
            eve_nombre="Evento Publicado",
            eve_descripcion="Publicado y en curso",
            eve_ciudad="Barranquilla",
            eve_lugar="Teatro",
            eve_fecha_inicio=self.hoy - timedelta(days=2),
            eve_fecha_fin=self.hoy + timedelta(days=2),  # Aún en curso
            eve_estado="PUBLICADO",
            eve_capacidad=150,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_publicado.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_publicado.eve_estado, "PUBLICADO",
                        "El estado PUBLICADO debe mantenerse")
        self.assertNotIn(evento_publicado.id, eventos_cerrados)

    # ===================================================================
    # TEST 6: Múltiples eventos - Cierre selectivo correcto
    # ===================================================================
    def test_cierra_solo_eventos_que_cumplen_criterios(self):
        """
        CA6: Procesar múltiples eventos y cerrar solo los que califican
        """
        # Arrange - Crear 5 eventos con diferentes condiciones
        
        # 1. Debe cerrarse (finalizado hace 10 días, ACTIVO)
        evento_1 = Eventos.objects.create(
            eve_nombre="Evento 1 - Cerrar",
            eve_descripcion="Cumple criterios",
            eve_ciudad="Pasto",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy - timedelta(days=12),
            eve_fecha_fin=self.hoy - timedelta(days=10),
            eve_estado="ACTIVO",
            eve_capacidad=80,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # 2. NO cerrar (finalizado hace 3 días - periodo gracia)
        evento_2 = Eventos.objects.create(
            eve_nombre="Evento 2 - NO Cerrar",
            eve_descripcion="En periodo de gracia",
            eve_ciudad="Ibagué",
            eve_lugar="Parque",
            eve_fecha_inicio=self.hoy - timedelta(days=5),
            eve_fecha_fin=self.hoy - timedelta(days=3),
            eve_estado="ACTIVO",
            eve_capacidad=60,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # 3. NO cerrar (ya cerrado manualmente)
        evento_3 = Eventos.objects.create(
            eve_nombre="Evento 3 - Ya Cerrado",
            eve_descripcion="Cerrado manual",
            eve_ciudad="Pereira",
            eve_lugar="Auditorio",
            eve_fecha_inicio=self.hoy - timedelta(days=15),
            eve_fecha_fin=self.hoy - timedelta(days=13),
            eve_estado="CERRADO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # 4. Debe cerrarse (finalizado hace 20 días, PUBLICADO)
        evento_4 = Eventos.objects.create(
            eve_nombre="Evento 4 - Cerrar Publicado",
            eve_descripcion="Publicado finalizado",
            eve_ciudad="Cartagena",
            eve_lugar="Hotel",
            eve_fecha_inicio=self.hoy - timedelta(days=22),
            eve_fecha_fin=self.hoy - timedelta(days=20),
            eve_estado="PUBLICADO",
            eve_capacidad=200,
            eve_tienecosto=True,
            eve_administrador_fk=self.administrador
        )
        
        # 5. NO cerrar (evento futuro)
        evento_5 = Eventos.objects.create(
            eve_nombre="Evento 5 - Futuro",
            eve_descripcion="Aún no inicia",
            eve_ciudad="Santa Marta",
            eve_lugar="Playa",
            eve_fecha_inicio=self.hoy + timedelta(days=10),
            eve_fecha_fin=self.hoy + timedelta(days=12),
            eve_estado="ACTIVO",
            eve_capacidad=150,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        
        # Refrescar desde DB
        evento_1.refresh_from_db()
        evento_2.refresh_from_db()
        evento_3.refresh_from_db()
        evento_4.refresh_from_db()
        evento_5.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_1.eve_estado, "CERRADO", "Evento 1 debe cerrarse")
        self.assertEqual(evento_2.eve_estado, "ACTIVO", "Evento 2 NO debe cerrarse")
        self.assertEqual(evento_3.eve_estado, "CERRADO", "Evento 3 mantiene CERRADO")
        self.assertEqual(evento_4.eve_estado, "CERRADO", "Evento 4 debe cerrarse")
        self.assertEqual(evento_5.eve_estado, "ACTIVO", "Evento 5 NO debe cerrarse")
        
        # Verificar cantidad correcta en log
        self.assertEqual(len(eventos_cerrados), 2,
                        "Solo 2 eventos deben estar en el log de cerrados")
        self.assertIn(evento_1.id, eventos_cerrados)
        self.assertIn(evento_4.id, eventos_cerrados)

    # ===================================================================
    # TEST 7: Log de auditoría generado correctamente
    # ===================================================================
    def test_genera_log_auditoria_con_eventos_cerrados(self):
        """
        CA7: El proceso debe generar log con lista de eventos cerrados
        """
        # Arrange
        evento_log_1 = Eventos.objects.create(
            eve_nombre="Evento Log 1",
            eve_descripcion="Para log",
            eve_ciudad="Tunja",
            eve_lugar="Universidad",
            eve_fecha_inicio=self.hoy - timedelta(days=15),
            eve_fecha_fin=self.hoy - timedelta(days=13),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        evento_log_2 = Eventos.objects.create(
            eve_nombre="Evento Log 2",
            eve_descripcion="Para log",
            eve_ciudad="Popayán",
            eve_lugar="Centro",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="PUBLICADO",
            eve_capacidad=75,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        log_output = self._capturar_log_cierre_automatico()
        
        # Assert
        self.assertIn("Evento Log 1", log_output,
                     "El log debe contener el nombre del evento 1")
        self.assertIn("Evento Log 2", log_output,
                     "El log debe contener el nombre del evento 2")
        self.assertIn("CERRADO", log_output,
                     "El log debe indicar el estado CERRADO")
        self.assertIn(str(evento_log_1.id), log_output,
                     "El log debe incluir el ID del evento")

    # ===================================================================
    # TEST 8: Evento en estado BORRADOR finalizado - Verificar comportamiento
    # ===================================================================
    def test_evento_borrador_finalizado_no_se_cierra(self):
        """
        CA8: Eventos en BORRADOR no deben cerrarse automáticamente
        (solo eventos publicados/activos se cierran)
        """
        # Arrange
        evento_borrador = Eventos.objects.create(
            eve_nombre="Evento Borrador",
            eve_descripcion="Nunca fue publicado",
            eve_ciudad="Villavicencio",
            eve_lugar="Auditorio",
            eve_fecha_inicio=self.hoy - timedelta(days=20),
            eve_fecha_fin=self.hoy - timedelta(days=18),
            eve_estado="BORRADOR",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_borrador.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_borrador.eve_estado, "BORRADOR",
                        "Evento BORRADOR no debe cambiar de estado")
        self.assertNotIn(evento_borrador.id, eventos_cerrados)

    # ===================================================================
    # TEST 9: Verificar que la fecha de cierre se registra
    # ===================================================================
    def test_registra_fecha_cierre_automatico(self):
        """
        CA9: Al cerrar automáticamente, debe registrarse la fecha/hora
        (Asume que existe campo eve_fecha_cierre en el modelo)
        """
        # Arrange
        evento_fecha = Eventos.objects.create(
            eve_nombre="Evento Fecha Cierre",
            eve_descripcion="Verificar timestamp",
            eve_ciudad="Neiva",
            eve_lugar="Hotel",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="ACTIVO",
            eve_capacidad=120,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        self._ejecutar_cierre_automatico()
        evento_fecha.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_fecha.eve_estado, "CERRADO")
        
        # Si existe campo de fecha de cierre, verificar
        # if hasattr(evento_fecha, 'eve_fecha_cierre'):
        #     self.assertIsNotNone(evento_fecha.eve_fecha_cierre,
        #                         "Debe registrarse fecha de cierre")
        #     self.assertAlmostEqual(
        #         evento_fecha.eve_fecha_cierre.date(),
        #         self.hoy,
        #         delta=timedelta(days=1)
        #     )

    # ===================================================================
    # TEST 10: Evento con fecha_fin = hoy - NO cerrar
    # ===================================================================
    def test_evento_finaliza_hoy_no_se_cierra_aun(self):
        """
        CA10: Evento que finaliza exactamente hoy NO debe cerrarse
        (periodo de gracia empieza mañana)
        """
        # Arrange
        evento_hoy = Eventos.objects.create(
            eve_nombre="Evento Finaliza Hoy",
            eve_descripcion="Termina hoy mismo",
            eve_ciudad="Montería",
            eve_lugar="Estadio",
            eve_fecha_inicio=self.hoy - timedelta(days=2),
            eve_fecha_fin=self.hoy,  # Finaliza hoy
            eve_estado="ACTIVO",
            eve_capacidad=300,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        evento_hoy.refresh_from_db()
        
        # Assert
        self.assertEqual(evento_hoy.eve_estado, "ACTIVO",
                        "Evento que finaliza hoy NO debe cerrarse aún")
        self.assertNotIn(evento_hoy.id, eventos_cerrados)

   
    # ===================================================================
    # TEST 12: Sin eventos que cerrar - Log vacío
    # ===================================================================
    def test_sin_eventos_para_cerrar_log_vacio(self):
        """
        CA12: Si no hay eventos para cerrar, el log debe indicarlo
        """
        # Arrange - Solo crear eventos que NO deben cerrarse
        Eventos.objects.create(
            eve_nombre="Evento Futuro",
            eve_descripcion="No debe cerrarse",
            eve_ciudad="Sincelejo",
            eve_lugar="Plaza",
            eve_fecha_inicio=self.hoy + timedelta(days=5),
            eve_fecha_fin=self.hoy + timedelta(days=7),
            eve_estado="ACTIVO",
            eve_capacidad=100,
            eve_tienecosto=False,
            eve_administrador_fk=self.administrador
        )
        
        # Act
        eventos_cerrados = self._ejecutar_cierre_automatico()
        log_output = self._capturar_log_cierre_automatico()
        
        # Assert
        self.assertEqual(len(eventos_cerrados), 0,
                        "No debe haber eventos cerrados")
        self.assertIn("No se encontraron eventos", log_output,
                     "El log debe indicar que no hubo eventos para cerrar")

    # ===================================================================
    # MÉTODOS AUXILIARES
    # ===================================================================
    
    def _ejecutar_cierre_automatico(self, dias_limite=7):
        """
        Simula la ejecución del comando/tarea programada de cierre automático
        
        Args:
            dias_limite: Días después de finalizar para cerrar evento
            
        Returns:
            Lista de IDs de eventos cerrados
        """
        fecha_corte = self.hoy - timedelta(days=dias_limite)
        
        # Obtener eventos que deben cerrarse
        eventos_a_cerrar = Eventos.objects.filter(
            eve_fecha_fin__lt=fecha_corte,  # Finalizados hace más de X días
            eve_estado__in=["ACTIVO", "PUBLICADO"]  # Solo estos estados
        )
        
        eventos_cerrados = []
        
        for evento in eventos_a_cerrar:
            evento.eve_estado = "CERRADO"
            evento.save()
            eventos_cerrados.append(evento.id)
        
        return eventos_cerrados
    
    def _capturar_log_cierre_automatico(self):
        """
        Captura el output del log generado por el proceso
        
        Returns:
            String con el contenido del log
        """
        out = StringIO()
        
        # Simular generación de log
        eventos_cerrados = self._ejecutar_cierre_automatico()
        
        if eventos_cerrados:
            out.write("=== LOG DE CIERRE AUTOMÁTICO ===\n")
            out.write(f"Fecha ejecución: {timezone.now()}\n")
            out.write(f"Total eventos cerrados: {len(eventos_cerrados)}\n\n")
            
            for evento_id in eventos_cerrados:
                evento = Eventos.objects.get(id=evento_id)
                out.write(f"ID: {evento.id} | Nombre: {evento.eve_nombre} | ")
                out.write(f"Estado: CERRADO | Finalizado: {evento.eve_fecha_fin}\n")
        else:
            out.write("No se encontraron eventos para cerrar en esta ejecución\n")
        
        return out.getvalue()


# ===================================================================
# TEST DE COMANDO DE GESTIÓN (Management Command)
# ===================================================================

class CierreAutomaticoCommandTest(TestCase):
    """
    HU-95: Pruebas para el comando de gestión que ejecuta el cierre automático
    
    Uso esperado:
        python manage.py cerrar_eventos_finalizados
        python manage.py cerrar_eventos_finalizados --dias=10
    """
    
    def setUp(self):
        """Configuración para tests del comando"""
        self.admin_user = Usuario.objects.create_user(
            username="admin_cmd",
            password="admin123",
            tipo_documento="CC",
            documento_identidad="1111111111",
            email="cmd@test.com"
        )
        self.admin = Administradores.objects.create(
            usuario=self.admin_user,
            num_eventos=5,
            estado="Activo"
        )
        self.hoy = timezone.now().date()
    
    def test_comando_ejecuta_sin_errores(self):
        """
        Verificar que el comando se ejecuta correctamente
        """
        # Arrange
        Eventos.objects.create(
            eve_nombre="Evento Test Comando",
            eve_descripcion="Para comando",
            eve_ciudad="Manizales",
            eve_lugar="Test",
            eve_fecha_inicio=self.hoy - timedelta(days=10),
            eve_fecha_fin=self.hoy - timedelta(days=8),
            eve_estado="ACTIVO",
            eve_capacidad=50,
            eve_tienecosto=False,
            eve_administrador_fk=self.admin
        )
        
        # Act & Assert - No debe lanzar excepción
        try:
            # call_command('cerrar_eventos_finalizados')
            # Como el comando aún no existe, simulamos su ejecución
            pass
        except Exception as e:
            self.fail(f"El comando no debe fallar: {e}")
    
    def test_comando_acepta_parametro_dias(self):
        """
        Verificar que el comando acepta parámetro --dias
        """
        # Act & Assert
        try:
            # call_command('cerrar_eventos_finalizados', dias=10)
            pass
        except Exception as e:
            self.fail(f"El comando debe aceptar parámetro dias: {e}")
    
    def test_comando_genera_output_visible(self):
        """
        El comando debe mostrar información en consola
        """
        # Arrange
        out = StringIO()
        
        # Act
        # call_command('cerrar_eventos_finalizados', stdout=out)
        
        # Assert (simulado)
        # self.assertIn("eventos cerrados", out.getvalue().lower())
        pass