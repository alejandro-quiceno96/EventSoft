document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".btn-eliminar").forEach(button => {
        button.addEventListener("click", function () {
            eventoIdAEliminar = this.getAttribute("data-id");
            
            // Mostrar el modal de confirmación
            let modal = new bootstrap.Modal(document.getElementById("confirmarEliminarModal"));
            modal.show();
        });
    });

   document.getElementById("btnConfirmarEliminar").addEventListener("click", function () {
    if (eventoIdAEliminar) {
        let url = baseEliminarUrl + eventoIdAEliminar; // Importante terminar con "/"
        console.log("Eliminando evento en URL:", url);

        fetch(url)
        .then(response => response.json())
        .then(data => {
            alert(data.mensaje);
            location.reload();
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Hubo un error al eliminar el evento");
        });
    }
    });

});
