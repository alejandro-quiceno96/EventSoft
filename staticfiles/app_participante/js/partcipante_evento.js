document.addEventListener("DOMContentLoaded", function () {
  let eventoIdSeleccionado = null;
  let participanteIdSeleccionado = null;
    
  document.querySelectorAll(".btn-ver-mas").forEach(button => {
        button.addEventListener("click", function () {
            let eventoId = this.getAttribute("data-id");
            let participanteId = this.getAttribute("data-cedula")
            let url =  urlDetalleEvento.replace('/123/', `/${eventoId}/`).replace('/456', `/${participanteId}`);
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    eventoIdSeleccionado = data.eve_id;
                    participanteIdSeleccionado = data.cedula;
                    document.getElementById("modalNombre").textContent = data.eve_nombre;
                    document.getElementById("modalDescripcion").textContent = data.eve_descripcion;
                    document.getElementById("modalCiudad").textContent = data.eve_ciudad;
                    document.getElementById("modalLugar").textContent = data.eve_lugar;
                    document.getElementById("modalFecha").textContent = `${data.eve_fecha_inicio} - ${data.eve_fecha_fin}`;
                    document.getElementById("modalCategoria").textContent = data.eve_categoria;
                    document.getElementById("modalAforo").textContent = data.eve_cantidad;
                    document.getElementById("modalInscripcion").textContent = data.eve_costo;
                    document.getElementById("modalClave").textContent = data.eve_clave;
                    document.getElementById("modalImagen").src = data.eve_imagen;
                    document.getElementById("modalProyecto").textContent = data.proyecto;
                    document.getElementById("btnCriterios").setAttribute('data-evento-id', data.eve_id);
                    if (data.eve_informacion_tecnica) {
                        document.getElementById("modalTecnica").href = data.eve_informacion_tecnica;
                        document.getElementById("modalTecnicaDescargar").href = data.eve_informacion_tecnica;
                    } else {
                        document.getElementById("modalTecnicaLabel").textContent = "Información Técnica: No disponible";
                        document.getElementById("modalTecnica").style.display = "none";
                        document.getElementById("modalTecnicaDescargar").style.display = "none";
                    }

                    if (data.eve_programacion) {
                        document.getElementById("modalProgramacion").href = data.eve_programacion;
                        document.getElementById("modalProgramacionDescargar").href = data.eve_programacion;
                    } else {
                        document.getElementById("modalProgramacionLabel").textContent = "Programación: No disponible";
                        document.getElementById("modalProgramacion").style.display = "none";
                        document.getElementById("modalProgramacionDescargar").style.display = "none";
                    }

                    if (data.codigo_qr) {
                        document.getElementById("modalCodigoQr").href = data.codigo_qr;
                        document.getElementById("modalCodigoQrDescargar").href = data.codigo_qr;
                    } else {
                        document.getElementById("modalCodigoQrLabel").textContent = "Codigo Qr: No disponible";
                        document.getElementById("modalCodigoQr").style.display = "none";
                        document.getElementById("modalCodigoQrDescargar").style.display = "none";
                    }
                    // Mostrar el modal
                    const modalElement = document.getElementById('eventoModal');
                    if (modalElement) {
                        const modal = new bootstrap.Modal(modalElement, {
                        backdrop: 'static',
                        keyboard: false
                        });
                        modal.show();
                    }
                })
                .catch(error => console.error("Error al obtener los datos:", error));
        });
    });

  document.getElementById("btnAbrirConfirmarCancelar").addEventListener("click", function () {
    new bootstrap.Modal(document.getElementById("confirmarCancelarModal")).show();
  });

  document.querySelectorAll(".btn-cancelar").forEach(button => {
    button.addEventListener("click", function () {
      eventoIdSeleccionado = this.getAttribute("data-id");
      participanteIdSeleccionado = this.getAttribute("data-cedula");

      const confirmarModal = new bootstrap.Modal(document.getElementById("confirmarCancelarModal"));
      confirmarModal.show();
    });
  });

  document.querySelectorAll("modalProgramacionDescargar").forEach(button => {
    button.addEventListener("click", function () {
        enlace_programacion.download
    });
  });
  document.querySelectorAll("modalCodigoQrDescargar").forEach(button => {
    button.addEventListener("click", function () {
        enlace_qr.download
    });
  });

  document.getElementById("btnConfirmarCancelarInscripcion").addEventListener("click", function () {
    let url = urlEliminarInscripcion.replace('/123/', `/${eventoIdSeleccionado}/`).replace('/456', `/${participanteIdSeleccionado}`);
    console.log(url);
    const formData = new FormData();
    fetch(url, {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          location.reload();
        } else {
          alert("No se pudo cancelar.");
        }
      });
  });

  document.getElementById("btnAbrirEditar").addEventListener("click", function () {
    let url =  urlModificarInscripcion.replace('/123/', `/${participanteIdSeleccionado}/`).replace('/456', `/${eventoIdSeleccionado}`);
    fetch(url)
      .then(res => res.json())
      .then(data => {
           document.getElementById("inputNombre").value = data.nombre;
            document.getElementById("inputDescripcion").value = data.descripcion;
            if (data.documento) {
                document.getElementById("btn-ver-documento").href = data.documento;
            } else {
                document.getElementById("btn-ver-documento").style.display = "none";
            }

        new bootstrap.Modal(document.getElementById("modificarInscripcionModal")).show();
      });
  });

document.getElementById("formModificarInscripcion").addEventListener("submit", function (e) {
  e.preventDefault();

  const form = this;
  const formData = new FormData(form);
  formData.append("participante_id", participanteIdSeleccionado);

  let url = urlModificarParticipante
    .replace('/123/', `/${eventoIdSeleccionado}/`)
    .replace('/456', `/${participanteIdSeleccionado}`);

  fetch(url, {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Inscripción actualizada.");

        // ✅ Cerrar el modal correctamente
        const modal = bootstrap.Modal.getInstance(document.getElementById("modificarInscripcionModal"));
        modal.hide();
      } else {
        alert(data.error || "Error al actualizar.");
      }
    })
    .catch(err => {
      alert("Error al modificar inscripción.");
      console.error(err);
    });
});




  // 🔒 Volver a desactivar los inputs y limpiar el fondo oscuro al cerrar el modal
const modalModificar = document.getElementById("modificarInscripcionModal");

modalModificar.addEventListener("hidden.bs.modal", function () {

  // Limpiar fondo oscuro (backdrop)
  document.body.classList.remove("modal-open");
  document.querySelectorAll(".modal-backdrop").forEach(el => el.remove());

  // 🔹 Limpiar input de archivo
  const inputDocumento = this.querySelector("#inputDocumento");
  if (inputDocumento) {
    inputDocumento.value = ""; // Vacía el archivo seleccionado
  }

  // 🔹 Restaurar texto por defecto
  const fileNameSpan = this.querySelector(".file-name");
  if (fileNameSpan) {
    fileNameSpan.textContent = "No se ha seleccionado ningún archivo";
  }
});



  document.querySelectorAll(".btn-abrir-editar-externo").forEach(btn => {
    btn.addEventListener("click", function () {
      eventoIdSeleccionado = this.getAttribute("data-id");
      participanteIdSeleccionado = this.getAttribute("data-cedula")
      let url =  urlModificarInscripcion.replace('/123/', `/${participanteIdSeleccionado}/`).replace('/456', `/${eventoIdSeleccionado}`);
      fetch(url,{
      method: "POST",
    })
        .then(res => res.json())
        .then(data => {
          document.getElementById("modalProyecto").href =data.par_eve_evento_fk;
          document.getElementById("inputNombre").value = data.nombre;
          document.getElementById("inputDescripcion").value = data.descripcion;
          document.getElementById("btn-ver-documento").href = data.documento;
          new bootstrap.Modal(document.getElementById("modificarInscripcionModal")).show();
        });
    });
  });

  
});

document.getElementById('btnCriterios').addEventListener('click', function () {
  const eventoId = this.getAttribute('data-evento-id');
  const url = urlCriterios + eventoId;

  if (eventoId) {
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('modalCargaPDF'));
    modal.show();

    // Esperar un momento para que el modal se vea antes de abrir el PDF
    setTimeout(() => {
      window.open(url, '_blank');
      modal.hide();  // Ocultar modal luego de abrir el PDF
    }, 1000);  // Puedes ajustar el tiempo si lo deseas
  } else {
    alert("No se encontró el evento asociado");
  }
});


document.getElementById("inputDocumento").addEventListener("change", function () {
  const fileNameSpan = document.querySelector(".file-name");
  if (fileNameSpan) {
    fileNameSpan.textContent = this.files.length > 0
      ? this.files[0].name
      : "No se ha seleccionado ningún archivo";
  }
});



