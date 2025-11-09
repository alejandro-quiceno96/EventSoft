document.querySelectorAll('.btn-ver-estadisticas-evento').forEach(btn => {
    btn.addEventListener('click', function() {
        document.getElementById('modal-estadisticas-evento-titulo').textContent = "📊 " + this.dataset.eventoNombre;
        document.getElementById('modal-estadisticas-evento-lugar').textContent = this.dataset.lugar;
        document.getElementById('modal-estadisticas-evento-ciudad').textContent = this.dataset.ciudad;
        document.getElementById('modal-estadisticas-evento-fecha-inicio').textContent = this.dataset.fechaInicio;
        document.getElementById('modal-estadisticas-evento-fecha-fin').textContent = this.dataset.fechaFin;
        document.getElementById('modal-estadisticas-evento-inscritos').textContent = this.dataset.inscritos;
        document.getElementById('modal-estadisticas-evento-asistentes').textContent = this.dataset.asistentes;
        document.getElementById('modal-estadisticas-evento-participantes').textContent = this.dataset.participantes;
        document.getElementById('modal-estadisticas-evento-evaluadores').textContent = this.dataset.evaluadores;

        document.getElementById('modal-estadisticas-evento').style.display = 'block';
    });
});

// Cerrar modal
document.querySelector('.modal-estadisticas-evento-close').onclick = function() {
    document.getElementById('modal-estadisticas-evento').style.display = 'none';
};

// Cerrar al hacer click fuera
window.addEventListener('click', function(e) {
    if (e.target.id === 'modal-estadisticas-evento') {
        document.getElementById('modal-estadisticas-evento').style.display = 'none';
    }
});
