document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".btn-ver-mas").forEach(button => {
        button.addEventListener("click", function () {
            let eventoId = this.getAttribute("data-id");
           let url = baseEventoDetalleUrl + eventoId;
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
                    document.getElementById("modalParticipantes").textContent = data.cantidad_participantes;
                    document.getElementById("modalAsistentes").textContent = data.cantidad_asistentes;
                    document.getElementById("modalImagen").src = data.eve_imagen;
                    document.getElementById("btnAccion").setAttribute("data-id", data.eve_id);
                    document.getElementById("btnModificar").setAttribute("data-id", data.eve_id);
                    document.getElementById("btnCriterios").setAttribute("data-id", data.eve_id);
                    document.getElementById("btnCriterios").setAttribute("data-url", baseCriteriosUrl + data.eve_id);
                    // Mostrar el modal
                    new bootstrap.Modal(document.getElementById("eventoModal")).show();
                })
                .catch(error => console.error("Error al obtener los datos:", error));
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

