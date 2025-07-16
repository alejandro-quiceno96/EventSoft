const baseEventoDetalleUrl = "{% url 'administrador:evento_detalle' 0 %}".replace('0', '');
const baseEliminarUrl = "{% url 'administrador:eliminar_evento' 0 %}".replace('0', '');
const baseModificarUrl = "{% url 'administrador:editar_evento' 0 %}".replace('0', '');
const baseCriteriosUrl = "{% url 'administrador:criterios_evaluacion' 0 %}".replace('0', '');
const baseConfigCertificadosUrl = "{% url 'administrador:configuracion_certificados' 0 %}";

// Función para actualizar el estado visual de los botones
function actualizarEstadoBotones(evento) {
  const participantesHab = evento.participantes_habilitados;
  const participantesDes = evento.participantes_deshabilitados;
  const evaluadoresHab = evento.evaluadores_habilitados;
  const evaluadoresDes = evento.evaluadores_deshabilitados;
  
  // Actualizar contadores
  document.getElementById('participantesHabilitados').textContent = `${participantesHab} Habilitados`;
  document.getElementById('participantesDeshabilitados').textContent = `${participantesDes} Deshabilitados`;
  document.getElementById('evaluadoresHabilitados').textContent = `${evaluadoresHab} Habilitados`;
  document.getElementById('evaluadoresDeshabilitados').textContent = `${evaluadoresDes} Deshabilitados`;
  
  // Actualizar botón de participantes
  const btnParticipantes = document.getElementById('btnHabilitarParticipantes');
  const textoParticipantes = document.getElementById('textoParticipantes');
  
  if (participantesDes === 0 && participantesHab > 0) {
    btnParticipantes.className = 'btn w-100 btn-deshabilitado';
    textoParticipantes.textContent = 'Deshabilitar Participantes';
  } else if (participantesHab === 0 && participantesDes > 0) {
    btnParticipantes.className = 'btn w-100 btn-habilitado';
    textoParticipantes.textContent = 'Habilitar Participantes';
  } else {
    btnParticipantes.className = 'btn w-100 btn-mixto';
    textoParticipantes.textContent = 'Alternar Participantes';
  }
  
  // Actualizar botón de evaluadores
  const btnEvaluadores = document.getElementById('btnHabilitarEvaluadores');
  const textoEvaluadores = document.getElementById('textoEvaluadores');
  
  if (evaluadoresDes === 0 && evaluadoresHab > 0) {
    btnEvaluadores.className = 'btn w-100 btn-deshabilitado';
    textoEvaluadores.textContent = 'Deshabilitar Evaluadores';
  } else if (evaluadoresHab === 0 && evaluadoresDes > 0) {
    btnEvaluadores.className = 'btn w-100 btn-habilitado';
    textoEvaluadores.textContent = 'Habilitar Evaluadores';
  } else {
    btnEvaluadores.className = 'btn w-100 btn-mixto';
    textoEvaluadores.textContent = 'Alternar Evaluadores';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  // Datos de eventos con estado de habilitación
  const eventos = [
    {% for evento in eventos %}
    {
      id: {{ evento.id }},
      participantes_habilitados: {{ evento.participantes_habilitados|default:0 }},
      participantes_deshabilitados: {{ evento.participantes_deshabilitados|default:0 }},
      evaluadores_habilitados: {{ evento.evaluadores_habilitados|default:0 }},
      evaluadores_deshabilitados: {{ evento.evaluadores_deshabilitados|default:0 }}
    },
    {% endfor %}
  ];
  
  const botonesVerMas = document.querySelectorAll('.btn-ver-mas');
  
  botonesVerMas.forEach(btn => {
    btn.addEventListener('click', function () {
      const eventoId = btn.getAttribute('data-id');
      const evento = eventos.find(e => e.id == eventoId);
      
      if (evento) {
        // Establecer enlaces
        const linkParticipantes = document.getElementById('linkHabilitarParticipantes');
        const linkEvaluadores = document.getElementById('linkHabilitarEvaluadores');
        
        linkParticipantes.href = `/administrador/habilitar_participantes/${eventoId}/`;
        linkEvaluadores.href = `/administrador/habilitar_evaluadores/${eventoId}/`;
        
        // Actualizar estado visual
        actualizarEstadoBotones(evento);
        
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('eventoModal'));
        modal.show();
      }
    });
  });
  
  // Funcionalidad de estadísticas (conservada)
  document.getElementById('cerrarEstadisticas').addEventListener('click', () => {
    document.getElementById("modal-estadisticas").style.display = "none";
  });
  
  document.getElementById('modal-estadisticas').addEventListener('click', e => {
    if (e.target === e.currentTarget) {
      document.getElementById("modal-estadisticas").style.display = "none";
    }
  });
  
  document.querySelectorAll('.btn-estadisticas').forEach(button => {
    button.addEventListener('click', () => {
      const inscritos = button.dataset.inscritos || '0';
      const asistentes = button.dataset.asistentes || '0';
      const participantes = button.dataset.participantes || '0';
      const evaluadores = button.dataset.evaluadores || '0';
      const fechaInicio = button.dataset.fechaInicio || '';
      const fechaFin = button.dataset.fechaFin || '';
      const lugar = button.dataset.lugar || '';
      const ciudad = button.dataset.ciudad || '';
      
      document.getElementById('statInscritos').textContent = inscritos;
      document.getElementById('statAsistentes').textContent = asistentes;
      document.getElementById('statParticipantes').textContent = participantes;
      document.getElementById('statEvaluadores').textContent = evaluadores;
      document.getElementById('statFecha').textContent = `${fechaInicio} al ${fechaFin}`;
      document.getElementById('statLugar').textContent = lugar;
      document.getElementById('statCiudad').textContent = ciudad;
      
      document.getElementById("modal-estadisticas").style.display = "flex";
    });
  });
});
