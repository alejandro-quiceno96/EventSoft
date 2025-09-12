document.addEventListener("DOMContentLoaded", () => {
    // Detectar clic en botones de "Asignar Evaluadores"
    document.querySelectorAll(".btn-abrir-evaluadores").forEach(btn => {
        btn.addEventListener("click", function () {
            const eventoId = this.dataset.eventoId;
            const proyectoId = this.dataset.proyectoId;
            abrirModalAsignar(eventoId, proyectoId);
        });
    });
});

// --- Funciones que ya tienes ---
function abrirModalAsignar(eventoId, proyectoId) {
    const modal = document.getElementById("modalEvaluadores");
    modal.style.display = "block";
    urlFinal = urlListarEvaluadores.replace('123', eventoId).replace('456', proyectoId);

    fetch(urlFinal)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("tablaEvaluadores");
            tbody.innerHTML = "";

            if (data.evaluadores.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="text-center">No hay evaluadores disponibles</td></tr>`;
                return;
            }

            data.evaluadores.forEach(evaluador => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${evaluador.nombre}</td>
                    <td>${evaluador.area}</td>
                    <td class="text-center">
                        ${
                            evaluador.asignado
                            ? `<button class="btn btn-outline-danger btn-designar"
                                        data-evaluador-id="${evaluador.id}"
                                        data-evento-id="${eventoId}"
                                        data-proyecto-id="${proyectoId}">
                                    Cancelar Asiganción
                                </button>`
                            : `<button class="btn btn-primary btn-asignar"
                                        data-evaluador-id="${evaluador.id}"
                                        data-evento-id="${eventoId}"
                                        data-proyecto-id="${proyectoId}">
                                   Asignar
                               </button>`
                        }
                    </td>
                `;
                tbody.appendChild(row);
            });

            // Eventos para los botones de asignar
            document.querySelectorAll(".btn-designar").forEach(btn => {
                btn.addEventListener("click", function () {
                    designarEvaluador(this.dataset.evaluadorId, this.dataset.eventoId, this.dataset.proyectoId);
                });
            });

            // Eventos para los botones de asignar
            document.querySelectorAll(".btn-asignar").forEach(btn => {
                btn.addEventListener("click", function () {
                    asignarEvaluador(this.dataset.evaluadorId, this.dataset.eventoId, this.dataset.proyectoId);
                });
            });
        });
}

function cerrarModalAsignar() {
    document.getElementById("modalEvaluadores").style.display = "none";
}

function asignarEvaluador(evaluadorId, eventoId, proyectoId) {
    urlFinal = urlAsignarEvaluador.replace('123', eventoId).replace('456', proyectoId).replace('789', evaluadorId);
    fetch(urlFinal, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({}),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("✅ Evaluador asignado correctamente");
            abrirModalAsignar(eventoId, proyectoId); // recargar tabla
        } else {
            alert("⚠️ " + data.message);
        }
    });
}

function designarEvaluador(evaluadorId, eventoId, proyectoId) {
    urlFinal = urlDesignarEvaluador.replace('123', eventoId).replace('456', proyectoId).replace('789', evaluadorId);
    fetch(urlFinal, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({}),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Asignación cancelada correctamente");
            abrirModalAsignar(eventoId, proyectoId); // recargar tabla
        } else {
            alert("⚠️ " + data.message);
        }
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
