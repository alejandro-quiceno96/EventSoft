function showLoader() {
  const bg = document.getElementById("loader-bg") || document.getElementById("loader");
  if (bg) bg.classList.remove("d-none");
}
function hideLoader() {
  const bg = document.getElementById("loader-bg") || document.getElementById("loader");
  if (bg) bg.classList.add("d-none");
}

document.addEventListener('DOMContentLoaded', function () {

    let asistenteId = null;
    let eventoId = null;
    let urlBase = null;

    // Abrir modal admitir
    document.querySelectorAll('.btn-admitir').forEach(button => {
        button.addEventListener('click', function () {
            asistenteId = this.dataset.id;
            eventoId = this.dataset.evento;
            urlBase = this.dataset.url;

            document.getElementById('mensaje-admitir').innerText =
                `¿Estás seguro que deseas admitir a ${this.dataset.nombre}?`;
        });
    });

    // Confirmar admitir
    document.getElementById('confirmarAdmitir').addEventListener('click', function () {
        const url = urlBase.replace('0', asistenteId).replace('estado-placeholder', 'Admitido');

        const formData = new FormData();
        formData.append('evento_id', eventoId);
        showLoader();
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        }).then(data => {
            if (data?.status === 'error') {
                alert(data.message);
                hideLoader();
            }
        }).catch(error => {
            console.error('Error:', error);
            hideLoader();
        });
    });

    // Abrir modal rechazo
    document.querySelectorAll('.btn-rechazar').forEach(button => {
        button.addEventListener('click', function () {
            asistenteId = this.dataset.id;
            eventoId = this.dataset.evento;
            urlBase = this.dataset.url;

            document.getElementById('mensaje-rechazo').innerText =
                `¿Estás seguro que deseas rechazar a ${this.dataset.nombre}?`;
            
            // Limpiar el textarea del motivo
            document.getElementById('motivoRechazo').value = '';
        });
    });

    // Confirmar rechazo con validación del motivo
    document.getElementById('confirmarRechazo').addEventListener('click', function () {
        const motivo = document.getElementById('motivoRechazo').value.trim();

        if (!motivo) {
            alert('Por favor, escribe el motivo del rechazo.');
            document.getElementById('motivoRechazo').focus();
            return;
        }

        const url = urlBase.replace('0', asistenteId).replace('estado-placeholder', 'Rechazado');

        const formData = new FormData();
        formData.append('evento_id', eventoId);
        formData.append('motivo', motivo);  // Enviamos el motivo al backend
        showLoader();
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;

            } else {
                return response.json();
            }
        }).then(data => {
            if (data?.status === 'error') {
                alert(data.message);
                hideLoader();
            }
        }).catch(error => {
            console.error('Error:', error);
            hideLoader();
        });
    });
});

// Función para obtener CSRF desde las cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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
