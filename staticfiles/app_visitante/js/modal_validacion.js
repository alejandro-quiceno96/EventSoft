function mostrarModalError(mensaje) {
  const modal = document.getElementById("modalError");
  const texto = document.getElementById("modal-error-mensaje");
  if (modal && texto) {
    texto.textContent = mensaje || "Ocurrió un error.";
    modal.classList.add("show");
    modal.style.display = "flex";
  }
}

function cerrarModalError() {
  const modal = document.getElementById("modalError");
  if (modal) {
    modal.classList.remove("show");
    modal.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btnAdmin = document.getElementById("btn-admin-eventos");
  const modal = document.getElementById("modalClave");
  const formClave = document.getElementById("formClave");
  const inputClave = document.getElementById("clave-acceso");

  if (btnAdmin) {
    btnAdmin.addEventListener("click", function (e) {
      const estado = this.getAttribute("data-estado");
      if (estado === "Creado") {
        e.preventDefault();
        mostrarModalClave();
      }
    });
  }

  formClave.addEventListener("submit", async (e) => {
    e.preventDefault();
    const clave = inputClave.value.trim();
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Opcional: loader o deshabilitar botón
    try {
      const res = await fetch(UrlValidaradministrador, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({ clave }),
      });

      const data = await res.json();
      if (data.success) {
        // Redirigir si la clave fue correcta
        window.location.href = UrlAdministrador;
      } else {
        mostrarModalError("Clave incorrecta. Verifique e intente de nuevo.");
      }
    } catch (error) {
      console.error("Error al validar clave:", error);
      mostrarModalError("Ocurrió un error. Intente de nuevo más tarde.");
    }
  });
});

function mostrarModalClave() {
  const modal = document.getElementById("modalClave");
  if (modal) {
    modal.classList.add("show");
    modal.style.display = "flex";
  }
}

function cerrarModalClave() {
  const modal = document.getElementById("modalClave");
  if (modal) {
    modal.classList.remove("show");
    modal.style.display = "none";
  }
}
