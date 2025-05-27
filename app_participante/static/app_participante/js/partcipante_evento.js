<script>
document.addEventListener("DOMContentLoaded", function () {
    const cancelarButtons = document.querySelectorAll(".cancelar-btn");

    cancelarButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const participante_id = this.getAttribute("data-participante-id");
            const evento_id = this.getAttribute("data-evento-id");

            if (confirm("¿Estás seguro de que deseas cancelar la inscripción?")) {
                const url = "{% url 'cancelar_inscripcion' 'REEMPLAZAR_PAR' 0 %}"
                    .replace("REEMPLAZAR_PAR", participante_id)
                    .replace("/0/", "/" + evento_id + "/");

                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/json"
                    },
                })
                .then((response) => {
                    if (response.ok) {
                        location.reload();
                    } else {
                        alert("Error al cancelar la inscripción.");
                    }
                });
            }
        });
    });

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
});
</script>
