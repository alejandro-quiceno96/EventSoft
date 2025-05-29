document.addEventListener("DOMContentLoaded", function () {
    let eventoIdSeleccionado = null;
    let participanteIdSeleccionado = null;
    const enlace_programacion = document.getElementById("modalProgramacionDescargar");
    const enlace_qr = document.getElementById("modalCodigoQrDescargar");
    
    // Botones de ver más información del evento
    document.querySelectorAll(".btn-ver-mas").forEach(button => {
        button.addEventListener("click", function () {
            let eventoId = this.getAttribute("data-id");
            let cedulaParticipante = this.getAttribute("data-cedula");
            let url =  urlDetalleEvento.replace('/123/', `/${eventoId}/`).replace('/456', `/${cedulaParticipante}`);

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    document.getElementById("modalNombre").textContent = data.eve_nombre;
                    document.getElementById("modalDescripcion").textContent = data.eve_descripcion;
                    document.getElementById("modalCiudad").textContent = data.eve_ciudad;
                    document.getElementById("modalLugar").textContent = data.eve_lugar;
                    document.getElementById("modalFecha").textContent = `${data.eve_fecha_inicio} - ${data.eve_fecha_fin}`;
                    document.getElementById("modalCategoria").textContent = data.eve_categoria;
                    document.getElementById("modalAforo").textContent = data.eve_cantidad;
                    document.getElementById("modalInscripcion").textContent = data.eve_costo;
                    document.getElementById("modalClave").textContent = data.eve_clave_acceso;
                    document.getElementById("modalImagen").src = data.eve_imagen;
                    document.getElementById("modalProgramacion").href = data.eve_programacion;
                    document.getElementById("modalCodigoQr").href = data.codigo_qr;
                    enlace_programacion.href = data.eve_programacion;
                    enlace_qr.href = data.codigo_qr
                    eventoIdSeleccionado = data.eve_id;
                    participanteIdSeleccionado = cedulaParticipante;

                    const modalElement = document.getElementById('eventoModalD');
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

    // Abrir modal de confirmación desde el modal principal
    document.getElementById("btnAbrirConfirmarCancelar").addEventListener("click", function () {
        const confirmarModal = new bootstrap.Modal(document.getElementById("confirmarCancelarModal"));
        confirmarModal.show();
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
    
    // Botones de cancelar dentro de las tarjetas
    document.querySelectorAll(".btn-cancelar").forEach(button => {
        button.addEventListener("click", function () {
            eventoIdSeleccionado = this.getAttribute("data-id");
            participanteIdSeleccionado = this.getAttribute("data-cedula");

            const confirmarModal = new bootstrap.Modal(document.getElementById("confirmarCancelarModal"));
            confirmarModal.show();
        });
    });

    // Confirmar cancelación de inscripción
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

    document.getElementById("formModificarInscripcion").addEventListener("submit", function (e) {
    e.preventDefault();

    const form = this;

    // 🔓 Activar todos los inputs deshabilitados antes de enviar
    const camposDeshabilitados = form.querySelectorAll("input:disabled");
    camposDeshabilitados.forEach(campo => campo.disabled = false);

    const formData = new FormData(form);
    formData.append("participante_id", participanteIdSeleccionado);
    let url = urlGuardar + participanteIdSeleccionado;
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

  document.getElementById("btnAbrirEditar").addEventListener("click", function () {
    let url =  urlModificar + participanteIdSeleccionado
    fetch(url)
      .then(res => res.json())
      .then(data => {
          document.getElementById("inputNombre").value = data.asi_nombre;
          document.getElementById("inputCorreo").value = data.asi_correo;
          document.getElementById("inputTelefono").value = data.asi_telefono;
          document.getElementById("modalProyecto").href =data.asi_eve_evento_fk;

        new bootstrap.Modal(document.getElementById("modificarInscripcionModal")).show();
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
});
