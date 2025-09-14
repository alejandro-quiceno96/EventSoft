document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".btn-ver-mas").forEach((button) => {
    button.addEventListener("click", function () {
      let eventoId = this.getAttribute("data-id");
      let url = baseEventoDetalleUrl + eventoId;
      const fichaTecnicaSubida = document.getElementById('fichaTecnicaSubida');
      const linkMemorias = document.getElementById("linkMemorias");
      const inputMemorias = document.getElementById("url_memorias");
      const btnSubirtecnica = document.getElementById("SubirFichaTecnica");

      fetch(url)
        .then((response) => response.json())
        .then((data) => {
          document.getElementById("modalNombre").textContent = data.eve_nombre;
          document.getElementById("modalDescripcion").textContent =
            data.eve_descripcion;
          document.getElementById("modalCiudad").textContent = data.eve_ciudad;
          document.getElementById("modalLugar").textContent = data.eve_lugar;
          document.getElementById(
            "modalFecha"
          ).textContent = `${data.eve_fecha_inicio} - ${data.eve_fecha_fin}`;
          document.getElementById("modalCategoria").textContent =
            data.eve_categoria;
          document.getElementById("modalAforo").textContent = data.eve_cantidad;
          document.getElementById("modalInscripcion").textContent =
            data.eve_costo;
          document.getElementById("modalParticipantes").textContent =
            data.cantidad_participantes;
          document.getElementById("modalAsistentes").textContent =
            data.cantidad_asistentes;
          document.getElementById("modalIdMemorias").value = data.eve_id;
          document.getElementById("modalImagen").src = data.eve_imagen;
          if (data.memorias) {

            // En el modal, mostrar input con lápiz para editar
                linkMemorias.innerHTML = `
                
                <a href="${data.memorias}" target="_blank" class="btn btn-primary mb-3">
                <i class="fa-solid fa-file-arrow-down"></i> Ver memorias del evento
            </a>`;
            inputMemorias.value = data.memorias;
          }
          document.getElementById("switchEvaluador").setAttribute("data-evento-id", eventoId);
          document.getElementById("switchExpositor").setAttribute("data-evento-id", eventoId);
          document.getElementById("switchEvaluador").checked = data.inscripcion_evaluador === true;
          document.getElementById("switchExpositor").checked = data.inscripcion_expositor === true;
          document.getElementById("confirmYes").setAttribute("data-evento-id", eventoId);
          document
            .getElementById("btnAccion")
            .setAttribute("data-id", data.eve_id);
          document
            .getElementById("btnModificar")
            .setAttribute("data-id", data.eve_id);
          document
            .getElementById("btnCriterios")
            .setAttribute("data-id", data.eve_id);
          document
            .getElementById("btnCriterios")
            .setAttribute("data-url", baseCriteriosUrl + data.eve_id);
          if (data.certificado) {
            document
              .getElementById("btnConfigCertificados")
              .setAttribute(
                "data-url",
                baseModificarCertificadosUrl.replace("0", data.eve_id)
              );
          } else {
            document
              .getElementById("btnConfigCertificados")
              .setAttribute(
                "data-url",
                baseConfigCertificadosUrl.replace("0", data.eve_id)
              );
          }
          btnSubirtecnica.setAttribute("data-evento-id", data.eve_id);
          if (data.ficha_tecnica) {
            fichaTecnicaSubida.innerHTML = `
            <span class="text-success">Ficha técnica subida:</span>
                <a href="${data.ficha_tecnica}" target="_blank" class="btn-compartir mb-3">
                <i class="fa-solid fa-file-arrow-down"></i> Ver ficha técnica subida
            </a>`;
          } else {
            fichaTecnicaSubida.innerHTML = `
                <span class="text-danger">No se ha subido una ficha técnica.</span>`;
          }

          // Mostrar el modal
          new bootstrap.Modal(document.getElementById("eventoModal")).show();
        })
        .catch((error) => console.error("Error al obtener los datos:", error));
    });
    
  });
});

document.getElementById("btnCriterios").addEventListener("click", function () {
  const url = this.getAttribute("data-url");
  if (url) {
    // Redirige a la URL de la ruta Flask
    window.location.href = url;
  }
});

document
  .getElementById("btnConfigCertificados")
  .addEventListener("click", function () {
    const url = this.getAttribute("data-url");
    if (url) {
      // Redirige a la URL de la ruta Flask
      window.location.href = url;
    }
  });

document.getElementById('btnSubirMemorias').addEventListener('click', function() {
    // Cerrar el modal actual
    var eventoModal = bootstrap.Modal.getInstance(document.getElementById('eventoModal'));
    if (eventoModal) {
        eventoModal.hide();
    }
    
    // Abrir el modal de memorias después de un pequeño delay
    setTimeout(function() {
        var memoriasModal = new bootstrap.Modal(document.getElementById('modalSubirMemorias'));
        memoriasModal.show();
    }, 300);
});

const eventoModal = document.getElementById("eventoModal");

eventoModal.addEventListener("hidden.bs.modal", () => {
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => backdrop.remove());
});
