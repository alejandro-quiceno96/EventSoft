function sumarMeses(fecha, meses) {
  const nuevaFecha = new Date(fecha);
  nuevaFecha.setMonth(nuevaFecha.getMonth() + meses);
  return nuevaFecha;
}



function formatearFechaISO(fecha) {
  return fecha.toISOString().split('T')[0];
}

function abrirModalAsignacion(btn) {
  const nombre = btn.getAttribute("data-nombre");
  const id = btn.getAttribute("data-id");

  document.getElementById("nombreUsuarioModal").textContent = nombre;
  document.getElementById("usuarioId").value = id;

  // Generar código aleatorio
  const caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let codigo = "";
  for (let i = 0; i < 8; i++) {
    codigo += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
  }
  document.getElementById("codigoAcceso").value = codigo;

  // Asignar fecha actual + 2 meses
  const fechaActual = new Date();
  const fechaLimite = sumarMeses(fechaActual, 2);
  document.getElementById("fechaLimiteRol").value = formatearFechaISO(fechaLimite);

  document.getElementById("modalConfirmar").classList.remove("d-none");
}

function cerrarModal() {
  document.getElementById("modalConfirmar").classList.add("d-none");
}

function mostrarLoader() {
  document.getElementById("loader-bg").classList.remove("d-none");
}
function ocultarLoader() {
  document.getElementById("loader-bg").classList.add("d-none");
}

function mostrarModalError(mensaje) {
  const modalElement = document.getElementById("modalError");
  const mensajeElement = document.getElementById("mensaje-error-modal");

  if (mensajeElement && mensaje) {
    mensajeElement.textContent = mensaje;
  }

  const modal = new bootstrap.Modal(modalElement);
  modal.show();
}
function mostrarModalExito(mensaje = "¡Acción realizada con éxito!") {
  const modal = new bootstrap.Modal(document.getElementById('modalExito'));
  document.querySelector('#modalExito .mensaje-exito').textContent = mensaje;
  modal.show();
}


document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("formAsignacion");
  const modalConfirmacion = new bootstrap.Modal(document.getElementById("modalConfirmacionFinal"));
  const modalExito = new bootstrap.Modal(document.getElementById("modalExito"));

  let formDataToSend = null; // almacenará los datos al dar click en "Asignar"

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    formDataToSend = new FormData(form);  // Guarda temporalmente
    modalConfirmacion.show(); // Abre modal de confirmación
  });

  document.getElementById("btnConfirmarAsignacionFinal").addEventListener("click", () => {
    modalConfirmacion.hide();
    mostrarLoader();

    fetch(form.action, {
  method: "POST",
  body: formDataToSend,
  headers: {
    "X-Requested-With": "XMLHttpRequest"
  }
})
.then(response => {
  console.log(response.status);  // Verifica código HTTP
  if (!response.ok) throw new Error("Error en la asignación");
  return response.json();
})
.then(data => {
  if (data.success) {
    ocultarLoader();
    cerrarModal();

    // Mostrar el modal de éxito
    const modalExito = new bootstrap.Modal(document.getElementById("modalExito"));
    modalExito.show();

    // Recarga la página después de 2 segundos
    setTimeout(() => window.location.reload(), 2000);
  } else {
    throw new Error("Respuesta sin éxito");
  }
})
.catch(async error => {
  ocultarLoader();
  const responseText = await error.response?.text?.() || "Sin detalles del servidor";
  alert("Ocurrió un error al asignar el rol.\n" + responseText);
  console.error("Error detallado:", responseText);
});
    });
    // 👇 Agrega esto para cambiar entre secciones
  const btnUsuarios = document.getElementById("btnUsuarios");
  const btnAdmins = document.getElementById("btnAdmins");
  const usuariosSection = document.getElementById("usuariosSection");
  const adminsSection = document.getElementById("adminsSection");

  btnUsuarios.addEventListener("click", () => {
    usuariosSection.classList.remove("d-none");
    adminsSection.classList.add("d-none");
    btnUsuarios.classList.add("active");
    btnAdmins.classList.remove("active");
  });

  btnAdmins.addEventListener("click", () => {
    adminsSection.classList.remove("d-none");
    usuariosSection.classList.add("d-none");
    btnAdmins.classList.add("active");
    btnUsuarios.classList.remove("active");
  });
});

function abrirModalCancelarAdmin(btn) {
  const adminId = btn.getAttribute("data-id");
  const input = document.getElementById("admin-id-cancelar");

  if (input) {
    input.value = adminId;
    const modalElement = document.getElementById("modalCancelarAdmin");

    // ✅ Asegurarte de que no tenga aria-hidden=true cuando se abre
    const modalInstance = new bootstrap.Modal(modalElement);
    modalInstance.show();
  }
}


function cerrarModalCancelarAdmin() {
  document.getElementById("modalCancelarAdmin").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formCancelarAdmin");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const adminId = document.getElementById("admin-id-cancelar").value;
      const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
      mostrarLoader();
      try {
        const res = await fetch(UrlcancelarAdmin, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify({ admin_id: adminId }),
        });

        const data = await res.json();
        if (data.success) {
          ocultarLoader();
          cerrarModalCancelarAdmin();
          mostrarModalExito("Administrador cancelado correctamente.");
          // Recarga la página después de 2 segundos
          setTimeout(() => window.location.reload(), 1000);
        } else {
          mostrarModalError(
            "No se pudo cancelar el administrador. ¡Intenta nuevamente.!"
          );

        }
      } catch (error) {
        console.error("Error:", error);
        mostrarModalError("Ha ocurrido un error. ¡Intenta mas tarde!");

      }
    });
  }
});

function filtrarPorCedula(valor) {
  const filtro = valor.toLowerCase();
  const filas = document.querySelectorAll(".tabla-usuarios tbody tr");

  filas.forEach(fila => {
    const cedula = fila.cells[0]?.textContent?.toLowerCase() || "";

    if (cedula.includes(filtro)) {
      fila.style.display = "";
    } else {
      fila.style.display = "none";
    }
  });
}

