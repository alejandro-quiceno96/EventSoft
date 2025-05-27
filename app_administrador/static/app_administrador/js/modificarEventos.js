document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".btn-ver-mas").forEach(button => {
        button.addEventListener("click", function () {
            let eventoId = this.getAttribute("data-id");
            document.getElementById("btnModificar").setAttribute("data-id", eventoId);
        });
    });

    document.getElementById("btnModificar").addEventListener("click", function () {
        const eventoId = this.getAttribute("data-id");
        const url = baseModificarUrl + eventoId;
        console.log("URL de modificación:", url);
        if (url) {
            window.location.href = url;
            
        } else {
            alert("⚠️ No se pudo construir la URL de modificación.");
        }
    });
});


function toggleCantidadParticipantesModificar() {
    const select = document.getElementById("permitir_participantes");
    const divCantidad = document.getElementById("cantidad_participantes_div");
    const inputCantidad = document.getElementById("cantidad_personas");

    const valor = select.value.trim().toLowerCase(); // normaliza

    if (valor === "si") {
        divCantidad.style.display = "block";
    } else {
        console.log("No se permite la cantidad de participantes");
        divCantidad.style.display = "none";
        inputCantidad.value = "";
    }
}

// Abre el modal cuando la página cargue si el evento fue modificado correctamente
window.addEventListener("DOMContentLoaded", toggleCantidadParticipantesModificar);
