document.addEventListener('DOMContentLoaded', function () {
  const botonPreinscripcion = document.getElementById('btn-preinscripcion');
  const linkDocumento = document.getElementById('link-documento');
  const sinDocumento = document.getElementById('sin-documento');
  const form = document.getElementById('formPreinscripcion');

  botonPreinscripcion.addEventListener('click', function (e) {
    e.preventDefault();
    const eventoId = this.dataset.evento;
    const evaluadorId = this.dataset.evaluador;
    const modal = new bootstrap.Modal(document.getElementById('modalPreinscripcion'));
    modal.show();
    const url = urlPreinscripcion.replace("123", eventoId).replace("456", evaluadorId);
    fetch(url)
      .then(response => response.json())
      .then(data => {
        if (data.documento) {
          linkDocumento.href = data.documento;
          linkDocumento.style.display = 'inline-block';
          sinDocumento.style.display = 'none';
        } else {
          linkDocumento.style.display = 'none';
          sinDocumento.style.display = 'block';
        }

        const urlModificar = urlModificarPreinscripcion.replace("123", eventoId).replace("456", evaluadorId);
        form.action = urlModificar;
      })
      .catch(error => {
        console.error("Error cargando datos:", error);
      });
  });
});

document.getElementById('documento').addEventListener('change', function () {
    const archivo = this.files[0];
    const nombreArchivo = document.getElementById('nombre-archivo');

    if (archivo) {
        nombreArchivo.textContent = `Archivo seleccionado: ${archivo.name}`;
        nombreArchivo.style.display = 'block';
    } else {
        nombreArchivo.textContent = '';
        nombreArchivo.style.display = 'none';
    }
});