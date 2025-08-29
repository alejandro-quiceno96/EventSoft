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
    const select = document.getElementById("permitir_participantes_mod");
    const divCantidad = document.getElementById("cantidad_participantes_div_mod");
    const inputCantidad = document.getElementById("cantidad_personas_mod");

    const valor = select.value.trim();
    if (valor === "si") {
        divCantidad.style.display = "block";
    } else {
        divCantidad.style.display = "none";
        inputCantidad.value = "";
    }
}


// Abre el modal cuando la página cargue si el evento fue modificado correctamente
window.addEventListener("DOMContentLoaded", toggleCantidadParticipantesModificar);
