document.addEventListener("DOMContentLoaded", () => {
  let pendingSwitch = null;
  const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
  let eventoId = 0;

  // Función para obtener CSRF Token de Django
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  // Función para mandar AJAX al backend
  function sendConfig(url, estado, role) {
    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ estado: estado, tipo : role}),
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log(`✔ ${role} actualizado: ${estado}`);
        } else {
          console.error(`❌ Error: ${data.message}`);
        }
      })
      .catch(error => console.error("Error en la petición:", error));
  }

  // Detectar cambios en los switches
  document.querySelectorAll('.toggle-switch').forEach(sw => {
    sw.addEventListener('change', function () {
        const evento_id = this.dataset.eventoId;
        eventoId = evento_id; // Verificar que se obtiene el ID correctamente
        const url = baseConfigInscripcionUrl.replace('0', evento_id);
        const role = this.dataset.role;

      if (!this.checked) {
        // Si lo desactivan → pedir confirmación
        pendingSwitch = this;
        document.getElementById("confirmMessage").innerText =
          `¿Seguro que deseas inactivar la inscripción de ${role}?`;
        confirmModal.show();
      } else {
        // Activar directamente (1)
        sendConfig(url, 1, role);
      }
    });
  });

  // Si confirman inactivar
  document.getElementById("confirmYes").addEventListener("click", function () {
    if (pendingSwitch) {
        const evento_id = this.dataset.eventoId; // aquí sí funciona con "this"
        const url = baseConfigInscripcionUrl.replace('0', evento_id);
        const role = pendingSwitch.dataset.role;
        sendConfig(url, 0, role);
        pendingSwitch = null;
    }
    confirmModal.hide();
});


  // Si cancelan, revertimos el switch
  document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
    if (pendingSwitch) {
      pendingSwitch.checked = true;
      pendingSwitch = null;
    }
  });
});
