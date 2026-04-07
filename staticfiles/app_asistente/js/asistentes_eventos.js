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
                    
                    document.getElementById("modalCodigoQr").href = data.codigo_qr;
                    
                    enlace_qr.href = data.codigo_qr
                    eventoIdSeleccionado = data.eve_id;
                    participanteIdSeleccionado = cedulaParticipante;

                    if (data.eve_programacion){
                        document.getElementById("modalProgramacion").href = data.eve_programacion;
                        enlace_programacion.href = data.eve_programacion;
                    }

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

 
});

function abrirCompartir(nombre, fechaInicio, fechaFin, enlace) {
    
    const url = urlDetalle.replace('/123', `/${enlace}`);
    const urlfull =  window.location.origin + url;
    const mensaje = `📢 ¡Te invito al evento "${nombre}"! 📅 Del ${fechaInicio} al ${fechaFin}. 🌐 Más información: ${urlfull}`;
    
    // Mostrar mensaje dentro del modal
    document.getElementById('mensajeEvento').innerText = mensaje;

    // Configurar enlace de WhatsApp
    document.getElementById('btnWhatsapp').href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;

    // Configurar enlace de Facebook
    document.getElementById('btnFacebook').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(enlace)}`;

    // Acción de copiar enlace
    document.getElementById('btnCopiar').onclick = function() {
        navigator.clipboard.writeText(urlfull).then(() => {
            alert("Enlace copiado al portapapeles ✅");
        }).catch(() => {
            alert("Error al copiar el enlace ❌");
        });
    };

    // Abrir modal
    let modal = new bootstrap.Modal(document.getElementById('modalCompartir'));
    modal.show();
}

