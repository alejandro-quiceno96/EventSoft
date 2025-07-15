document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".btn-ver-mas").forEach((button) => {
        button.addEventListener("click", function () {
            let eventoId = this.getAttribute("data-id");
            let url = baseEventoDetalleUrl + eventoId;;
            const contenedorMemorias = document.getElementById("modalMemorias");
            const linkMemorias = document.getElementById("linkMemorias");

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
                    document.getElementById("modalIdMemorias").value =
                        data.eve_id;
                    document.getElementById("modalImagen").src = data.eve_imagen;
                    console.log("Memorias URL:", data.memorias);
                    if (data.memorias) {
                        contenedorMemorias.innerHTML = `
                        <a href="${data.memorias}" target="_blank" class="btn btn-primary">
                        <i class="fa-solid fa-file-arrow-down"></i> Ver memorias del evento
                        </a>
            `;
                        linkMemorias.innerHTML = `
                        <a href="${data.memorias}" target="_blank" class="btn btn-primary">
                        <i class="fa-solid fa-file-arrow-down"></i> Ver memorias del evento
                        </a>
            `;
                    } else {
                        contenedorMemorias.innerHTML = `
                <p class="text-muted">No se ha subido memorias del evento.</p>
            `;
                        linkMemorias.innerHTML = `
                <p class="text-muted">No se ha subido memorias del evento.</p>
            `;
                    }
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
                    document
                        .getElementById("btnConfigCertificados")
                        .setAttribute("data-url", baseConfigCertificadosUrl.replace("0", data.eve_id));
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

document.getElementById("btnConfigCertificados").addEventListener("click", function () {
    const url = this.getAttribute("data-url");
    if (url) {
        // Redirige a la URL de la ruta Flask
        window.location.href = url;
    }
});
