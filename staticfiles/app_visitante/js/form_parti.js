document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("pro_documentos");
  const fileNameDisplay = document.querySelector(".file-name");
  const radios = document.querySelectorAll("input[name='opcion']");
  const btnBuscar = document.getElementById("btn-buscar-proyecto");
  const inputCodigo = document.getElementById("codigo_proyecto");
  const btnCerrarEncontrado = document.getElementById("btnCerrarEncontrado");
  const btnCerrarNo = document.getElementById("btnCerrarNo");
  const btnAsociar = document.getElementById("btnAsociar");
  const inputProyectoId = document.getElementById("proyecto_id");

  // Mostrar archivo seleccionado
  if (fileInput && fileNameDisplay) {
    fileInput.addEventListener("change", () => {
      const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : "Ningún archivo seleccionado";
      fileNameDisplay.textContent = `Archivo seleccionado: ${fileName}`;
    });
  }

  // Cambiar entre asociar / inscribir (radios)
  radios.forEach(radio => {
    radio.addEventListener("change", (e) => {
      if (e.target.value === "asociar") {
        mostrarFormulario("asociar");
        inputCodigo.required = true;
        document.getElementById("pro_nombre_input").required = false;
        document.getElementById("pro_descripcion_input").required = false;
        document.getElementById("pro_documentos").required = false;
      } else if (e.target.value === "inscribir") {
        mostrarFormulario("inscribir");
        inputCodigo.required = false;
        document.getElementById("pro_nombre_input").required = true;
        document.getElementById("pro_descripcion_input").required = true;
        document.getElementById("pro_documentos").required = true;
      }
    });
  });

  // Buscar proyecto
  btnBuscar.addEventListener("click", function () {
    const codigo = document.getElementById("codigo_proyectos").value.trim();

    if (codigo === "") {
      alert("Por favor ingrese un código de proyecto.");
      return;
    }

    fetch(`${urlBuscarProyecto.replace('CODIGO_TEMPORAL', codigo)}`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Error en la respuesta del servidor");
        }
        return response.json();
      })
      .then(data => {
        if (data.existe) {
          // Insertar datos en el modal
          document.getElementById("nombre_proyecto").textContent = data.proyecto.nombre;
          document.getElementById("codigo_proyecto").textContent = codigo;
          document.getElementById("descripcion_proyecto").textContent = data.proyecto.descripcion;
          document.getElementById("expositores_proyecto").textContent = data.proyecto.expositores;
          // Habilitar botón de asociar
          btnAsociar.disabled = false;
          btnAsociar.style.opacity = "1";
          btnAsociar.style.cursor = "pointer";
          // Asignar el ID del proyecto al input hidden
          inputProyectoId.value = data.proyecto.id;
          // Mostrar modal
          abrirModal("modalEncontrado");
        } else {
          // Deshabilitar botón de asociar
          btnAsociar.disabled = true;
          btnAsociar.style.opacity = "0.5";
          btnAsociar.style.cursor = "not-allowed";
          inputProyectoId.value = ""; // Limpiar el input hidden
          // Mostrar modal de no encontrado
          abrirModal("modalNoEncontrado");
        }
      })
      .catch(error => {
        console.error("Error:", error);
        abrirModal("modalNoEncontrado");
      });
  });

  btnCerrarNo.addEventListener("click", function() {
    cerrarModal("modalNoEncontrado");
  });
  btnCerrarEncontrado.addEventListener("click", function() {
    cerrarModal("modalEncontrado");
  });

  function abrirModal(id) {
    document.getElementById(id).classList.remove("hidden");
  }

  function cerrarModal(id) {
    document.getElementById(id).classList.add("hidden");
  }

  // 👉 Nueva función para mostrar formularios
  function mostrarFormulario(opcion) {
    // Ocultar ambos
    document.getElementById("form-asociar").classList.add("hidden");
    document.getElementById("form-inscribir").classList.add("hidden");

    // Mostrar el que corresponda
    if (opcion === "asociar") {
      document.getElementById("form-asociar").classList.remove("hidden");
    } else if (opcion === "inscribir") {
      document.getElementById("form-inscribir").classList.remove("hidden");
    }
  }
});
