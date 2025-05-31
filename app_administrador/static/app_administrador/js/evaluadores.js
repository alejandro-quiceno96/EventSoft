document.addEventListener("DOMContentLoaded", function () {
    let asistenteIdSeleccionado = null;
    let eventoIdSeleccionado = null;

    // 🟢 Evento para abrir el modal de admisión
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("btn-admitir")) {
            asistenteIdSeleccionado = event.target.getAttribute("data-id");
            eventoIdSeleccionado = event.target.getAttribute("data-evento");
            const asistenteNombre = event.target.getAttribute("data-nombre");

            document.getElementById("mensaje-admitir").innerText = 
                `¿Estás seguro de admitir a ${asistenteNombre}?`;
        }
    });

    // 🔴 Evento para abrir el modal de rechazo
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("btn-rechazar")) {
            asistenteIdSeleccionado = event.target.getAttribute("data-id");
            eventoIdSeleccionado = event.target.getAttribute("data-evento");
            const asistenteNombre = event.target.getAttribute("data-nombre");
            document.getElementById("mensaje-rechazo").innerText = 
                `¿Estás seguro de rechazar a ${asistenteNombre}?`;
        }
    });

    // 🟢 Evento para confirmar admisió
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("btn-confirmar-admitir")) {
            const urlAdmitir = event.target.getAttribute("data-url");
            console.log(urlAdmitir)
            if (asistenteIdSeleccionado && eventoIdSeleccionado) {
                actualizarEstado(asistenteIdSeleccionado, eventoIdSeleccionado, "Admitido", urlAdmitir);
            }
        }
    });

    // 🔴 Evento para confirmar rechazo
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("btn-confirmar-rechazar")) {
            const urlRechazar = event.target.getAttribute("data-url");
            if (asistenteIdSeleccionado && eventoIdSeleccionado) {
                actualizarEstado(asistenteIdSeleccionado, eventoIdSeleccionado, "Rechazado", urlRechazar);
            }
        }
    });

     function actualizarEstado(asistenteId, eventoId, nuevoEstado, urlTemplate) {
        const formData = new FormData();
        formData.append("evento_id", eventoId);
        console.log(`Actualizando estado de participante ${asistenteId} a ${nuevoEstado}`);
        const finalUrl = urlTemplate
            .replace("/0/", `/${asistenteId}/`)
            .replace("estado-placeholder", nuevoEstado);

        fetch(finalUrl, {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (res.ok) {
                location.reload();
            } else {
                throw new Error("Error en la solicitud");
            }
        })
        .catch(err => {
            console.error(err);
        });
    }
});
