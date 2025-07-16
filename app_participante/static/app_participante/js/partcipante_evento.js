document.addEventListener("DOMContentLoaded", function () {
  let eventoIdSeleccionado = null;
  let participanteIdSeleccionado = null;
    const enlace_programacion = document.getElementById("modalProgramacionDescargar");
    const enlace_qr = document.getElementById("modalCodigoQrDescargar");
    
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
                    document.getElementById("modalProgramacion").href = data.eve_programacion;
                    document.getElementById("modalCodigoQr").href = data.codigo_qr;
                    document.getElementById("modalTecnica").href = data.eve_informacion_tecnica;
                    document.getElementById("modalTecnicaDescargar").href = data.eve_informacion_tecnica;
                    document.getElementById("btnCriterios").setAttribute('data-evento-id', data.eve_id);
                    enlace_programacion.href = data.eve_programacion;
                    enlace_qr.href = data.codigo_qr
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

  document.getElementById("btnConfirmarCancelar").addEventListener("click", function () {
    let url = urlEliminarInscripcion.replace('/123/', `/${eventoIdSeleccionado}/`).replace('/456', `/${participanteIdSeleccionado}`);
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
    let url =  urlObtenerParticipante.replace('/123/', `/${participanteIdSeleccionado}/`).replace('/456', `/${eventoIdSeleccionado}`);
    fetch(url)
      .then(res => res.json())
      .then(data => {
          document.getElementById("modalProyecto").href =data.par_eve_evento_fk;

        new bootstrap.Modal(document.getElementById("modificarInscripcionModal")).show();
      });
  });

  document.getElementById("formModificarInscripcion").addEventListener("submit", function (e) {
    e.preventDefault();

    const form = this;

    // 🔓 Activar todos los inputs deshabilitados antes de enviar
    const camposDeshabilitados = form.querySelectorAll("input:disabled");
    camposDeshabilitados.forEach(campo => campo.disabled = false);

    const formData = new FormData(form);
    formData.append("participante_id", participanteIdSeleccionado);
    let url = urlModificarParticipante.replace('/123/', `/${eventoIdSeleccionado}/`).replace('/456', `/${participanteIdSeleccionado}`);
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
          alert("Error al actualizar.");
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
    // Desactivar inputs
    const inputs = this.querySelectorAll("input");
    inputs.forEach(input => input.disabled = true);

    // Limpiar fondo oscuro (backdrop)
    document.body.classList.remove("modal-open");
    document.querySelectorAll(".modal-backdrop").forEach(el => el.remove());
  });

  // ✏️ Activar campos cuando se hace clic en el botón de editar
  document.querySelectorAll(".btn-editar-campo").forEach(btn => {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input.disabled) {
        input.disabled = false;
        input.focus();
      }
    });
  });

  document.querySelectorAll(".btn-abrir-editar-externo").forEach(btn => {
    btn.addEventListener("click", function () {
      eventoIdSeleccionado = this.getAttribute("data-id");
      participanteIdSeleccionado = this.getAttribute("data-cedula")
      let url =  urlObtenerParticipante.replace('/123/', `/${participanteIdSeleccionado}/`).replace('/456', `/${eventoIdSeleccionado}`);
      console.log(url)
      fetch(url,{
      method: "POST",
    })
        .then(res => res.json())
        .then(data => {
          console.log(data)
          document.getElementById("modalProyecto").href =data.par_eve_evento_fk;

          new bootstrap.Modal(document.getElementById("modificarInscripcionModal")).show();
        });
    });
  });

  
});

document.getElementById('btnCriterios').addEventListener('click', function () {
  const eventoId = this.getAttribute('data-evento-id');
  const url = urlPdfCriterios + eventoId;

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


  


