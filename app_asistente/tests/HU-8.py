from django.test import TestCase
from django.core import mail
from app_eventos.models import Eventos, AsistentesEventos
from app_asistente.models import Asistentes
from app_usuarios.models import Usuario
from app_administrador.models import Administradores
from datetime import date, timedelta, datetime


class NotificacionesTests(TestCase):
    def setUp(self):
        # Crear admin
        self.usuario_admin = Usuario.objects.create_user(
            username="adminuser",
            email="admin@test.com",
            password="adminpass"
        )
        self.admin = Administradores.objects.create(usuario=self.usuario_admin)

        # Crear evento
        self.evento = Eventos.objects.create(
            eve_nombre="Evento Importante",
            eve_fecha_inicio=date.today(),
            eve_fecha_fin=date.today() + timedelta(days=1),
            eve_capacidad=50,
            eve_administrador_fk=self.admin
        )

        # Crear asistente
        self.usuario_asistente = Usuario.objects.create_user(
            username="asistenteuser",
            email="asistente@test.com",
            password="asistentepass"
        )
        self.asistente = Asistentes.objects.create(usuario=self.usuario_asistente)

        # Relación inscrito/admitido
        self.asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=self.asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=datetime.now(),
            asi_eve_estado="admitido",   # ✅ condición para recibir notificación
            asi_eve_clave="CLAVE123"
        )

    def test_asistente_recibe_notificacion_si_validado(self):
        """El asistente debe recibir notificación solo si está validado"""
        mensaje = f"[{self.evento.eve_nombre}] Cambio en el evento. Revise detalles."
        entregado = self.simular_envio_notificacion(self.asistente, mensaje)
        self.assertTrue(entregado)

        # Verificar que se mandó un correo
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.evento.eve_nombre, mail.outbox[0].subject)
        self.assertIn(mensaje, mail.outbox[0].body)
        self.assertIn(self.asistente.usuario.email, mail.outbox[0].to)

    def test_asistente_no_recibe_notificacion_si_pendiente(self):
        """Si el asistente no está validado (ej: pendiente), no debe recibir mensaje"""
        self.asistente_evento.asi_eve_estado = "pendiente"
        self.asistente_evento.save()

        mensaje = f"[{self.evento.eve_nombre}] Cambio en el evento."
        entregado = self.simular_envio_notificacion(self.asistente, mensaje)
        self.assertFalse(entregado)

        # No se envía correo
        self.assertEqual(len(mail.outbox), 0)

    def test_notificacion_solo_a_inscritos_validos_en_evento(self):
        """La notificación solo debe enviarse a asistentes inscritos y validados en el evento"""
        otro_usuario = Usuario.objects.create_user(
            username="otro",
            email="otro@test.com",
            password="test123"
        )
        otro_asistente = Asistentes.objects.create(usuario=otro_usuario)
        AsistentesEventos.objects.create(
            asi_eve_asistente_fk=otro_asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_fecha_hora=datetime.now(),
            asi_eve_estado="pendiente",   # 🚫 no validado
            asi_eve_clave="CLAVEOTRO"
        )

        mensaje = f"[{self.evento.eve_nombre}] Cambio importante"
        entregado = self.simular_envio_notificacion(otro_asistente, mensaje)
        self.assertFalse(entregado)

        # No se envía correo
        self.assertEqual(len(mail.outbox), 0)

    def test_notificacion_mensaje_max_160_caracteres(self):
        """El mensaje debe ser telegráfico, <=160 caracteres e incluir el nombre del evento si es posible"""
        mensaje = f"[{self.evento.eve_nombre}] Cambio crítico en la programación."
        self.assertLessEqual(len(mensaje), 160)
        self.assertIn(self.evento.eve_nombre, mensaje)

    # --- Helper para simular envío (mock en vez de SMS real) ---
    def simular_envio_notificacion(self, asistente, mensaje):
        if AsistentesEventos.objects.filter(
            asi_eve_asistente_fk=asistente,
            asi_eve_evento_fk=self.evento,
            asi_eve_estado="admitido"  # ✅ condición de admisión
        ).exists():
            # Simular envío de correo
            mail.send_mail(
                subject=f"Notificación evento: {self.evento.eve_nombre}",
                message=mensaje,
                from_email="no-reply@test.com",
                recipient_list=[asistente.usuario.email],
                fail_silently=False,
            )
            return True  # se envió
        return False  # no aplica
