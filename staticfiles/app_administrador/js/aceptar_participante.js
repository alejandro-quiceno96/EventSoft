// — utilidades para el loader —
function showLoader() {
  const bg = document.getElementById("loader-bg") || document.getElementById("loader");
  if (bg) bg.classList.remove("d-none");
}
function hideLoader() {
  const bg = document.getElementById("loader-bg") || document.getElementById("loader");
  if (bg) bg.classList.add("d-none");
}

// ✅ Obtener token CSRF
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    document.cookie.split(";").forEach(cookie => {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "="))
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
    });
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
  // 👉 Asegura que el loader esté oculto al iniciar
  hideLoader();

  // — Admisión directa —
  document.querySelectorAll(".btn-admitir").forEach(btn => {
    btn.addEventListener("click", function () {
      const pid = this.dataset.participanteId;
      const eid = this.dataset.eventoId;
      const tpl = this.dataset.url;
      actualizarEstado(pid, eid, "Admitido", tpl);
    });
  });

  // — Abrir modal de rechazo —
  document.querySelectorAll(".btn-rechazar").forEach(btn => {
    btn.addEventListener("click", function () {
      document.getElementById("participanteRechazoId").value = this.dataset.participanteId;
      const modal = new bootstrap.Modal(document.getElementById("modalRechazo"));
      modal.show();
    });
  });

  // — Confirmar rechazo —
  const btnRechazo = document.getElementById("btnRechazarConfirmacion");
  if (btnRechazo) {
    btnRechazo.addEventListener("click", function (e) {
      e.preventDefault(); // evita el envío normal del formulario

      const pid = document.getElementById("participanteRechazoId").value;
      const eid = document.querySelector('input[name="evento_id"]').value;
      const tpl = this.dataset.url;
      const razon = document.getElementById("razon-rechazo").value.trim();

      if (!razon) {
        alert("Por favor escribe la razón del rechazo.");
        return;
      }

      actualizarEstado(pid, eid, "Rechazado", tpl, razon);
      const modal = bootstrap.Modal.getInstance(document.getElementById("modalRechazo"));
      if (modal) modal.hide();
    });
  }

  // — Función genérica para actualizar estado —
  function actualizarEstado(pid, eid, nuevoEstado, tpl, razon = "") {
    const fd = new FormData();
    fd.append("evento_id", eid);
    if (nuevoEstado === "Rechazado") {
      fd.append("razon", razon);
    }

    const url = tpl
      .replace("/0/", `/${pid}/`)
      .replace("estado-placeholder", nuevoEstado);

    showLoader();
    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: fd
    })
      .then(res => {
        if (res.ok) {
          location.reload();
        } else {
          return res.json().then(data => {
            alert(data.message || "Error al actualizar el estado.");
            hideLoader();
          });
        }
      })
      .catch(err => {
        console.error("Error:", err);
        alert("Error de conexión al actualizar el estado.");
        hideLoader();
      });
  }
});

// Mostrar modal al hacer clic en el botón de certificados
const btnAbrirModal = document.getElementById("btnAbrirModalCertificados");
let modalConfirmacion;  // Variable para guardar el modal

btnAbrirModal.addEventListener('click', () => {
    if (fechaActual < eventoFechaFin) {
      const modalAdvertencia = new bootstrap.Modal(document.getElementById('modalFechaNoValida'));
      modalAdvertencia.show();
    } else {
      const modalConfirmacion = new bootstrap.Modal(document.getElementById('modalEnviarCertificados'));
      modalConfirmacion.show();
    }
  });

// Confirmar envío
const btnConfirmarEnvio = document.getElementById("btnConfirmarEnvioCertificados");
if (btnConfirmarEnvio) {
  btnConfirmarEnvio.addEventListener("click", function () {
    if (modalConfirmacion) {
      modalConfirmacion.hide();  // ✅ Cierra el modal antes de hacer fetch
    }

    showLoader();

    fetch(UrlEnvioCertificados, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")
      }
    })
    .then(res => {
      hideLoader();

      if (res.ok) {
        const modalExito = new bootstrap.Modal(document.getElementById("modalEnvioExitoso"));
        modalExito.show();
      } else {
        return res.json().then(data => {
          alert(data.message || "Error al enviar los certificados.");
        });
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("Error al conectar con el servidor.");
      hideLoader();
    });
  });
}
