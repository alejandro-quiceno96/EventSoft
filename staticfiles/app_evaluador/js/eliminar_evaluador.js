const btnCancelar = document.getElementById('btn-cancelar-inscripcion');
const formCancelar = document.getElementById('form-cancelar-inscripcion');

if (btnCancelar && formCancelar) {
    btnCancelar.addEventListener('click', function () {
      const eventoId = this.dataset.evento;
      const evaluadorId = this.dataset.evaluador;
      const url = urlCancelarInscripcion.replace("123", eventoId).replace("456", evaluadorId);
      formCancelar.action = url;
    });
}