function siguiente(pagina) {
    console.log(`Intentando pasar a la página ${pagina}`);

    // Obtener la página activa actual
    let paginaActual = document.querySelector(".pagina-activa");

    // Obtener todos los inputs, textareas y selects dentro de la página actual
    let inputs = paginaActual.querySelectorAll("input, textarea, select");

    // Verificar si hay algún campo vacío
    for (let input of inputs) {
        if (input.hasAttribute("required")) {
            let isEmpty = false;

            // Para inputs normales y textareas
            if (input.type === "text" || input.tagName === "TEXTAREA") {
                isEmpty = input.value.trim() === "";
            }

            // Para datetime-local, usar valueAsDate
            if (input.type === "datetime-local") {
                isEmpty = !input.value;
            }

            // Para selects, verificar que haya sido seleccionado un valor válido
            if (input.tagName === "SELECT") {
                isEmpty = input.value === "" || input.value === null;
            }

            if (isEmpty) {
                alert("Por favor, completa todos los campos antes de continuar.");
                input.focus(); // Enfoca el campo vacío
                return;
            }
        }
    }

    // Si todos los campos están llenos, cambiar de página
    paginaActual.classList.remove("pagina-activa");
    paginaActual.classList.add("pagina-inactiva");

    let nuevaPagina = document.getElementById("pagina" + pagina);
    nuevaPagina.classList.remove("pagina-inactiva");
    nuevaPagina.classList.add("pagina-activa");

    console.log(`Cambio a la página ${pagina} exitosamente`);
}

function volver(pagina) {
    console.log(`Volviendo a la página ${pagina}`);

    // Obtener la página activa actual
    let paginaActual = document.querySelector(".pagina-activa");

    // Cambiar la clase para ocultar la página actual
    paginaActual.classList.remove("pagina-activa");
    paginaActual.classList.add("pagina-inactiva");

    // Mostrar la página anterior
    let paginaAnterior = document.getElementById("pagina" + pagina);
    paginaAnterior.classList.remove("pagina-inactiva");
    paginaAnterior.classList.add("pagina-activa");
}

document.getElementById("area").addEventListener("change", function() {
    let areaId = this.value;
    let categoriaSelect = document.getElementById("categoria");
    console.log(areaId)
    categoriaSelect.innerHTML = '<option value="">Selecciona una categoría</option>';

    if (areaId) {
        fetch(`/get_categorias/${areaId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(categoria => {
                    let option = new Option(categoria.cat_nombre, categoria.cat_codigo);
                    categoriaSelect.add(option);
                });
            });
    }
});

function toggleCantidadParticipantes() {
    const select = document.getElementById('permitir_participantes');
    const cantidadDiv = document.getElementById('cantidad_participantes_div');

    if (select.value === '1') {
      cantidadDiv.style.display = 'block';
    } else {
      cantidadDiv.style.display = 'none';
    }
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("permitir_participantes").checked = false;
    toggleCantidadInput(); // Oculta el input al iniciar
  });

  function toggleCantidadInput() {
    const check = document.getElementById('permitir_participantes');
    const cantidadDiv = document.getElementById('cantidad_participantes_div');

    cantidadDiv.style.display = check.checked ? 'block' : 'none';
  }

function validarFecha() {
    const fechaInicio = document.getElementById("fecha_inicio").value;
    const fechaFin = document.getElementById("fecha_fin").value;

    if (fechaInicio && fechaFin) {
        const inicio = new Date(fechaInicio);
        const fin = new Date(fechaFin);

        if (inicio > fin) {
            alert("La fecha de inicio no puede ser posterior a la fecha de fin.");
            return false;
        }
    }
    return true;

} 

function actualizarContador() {
    const textarea = document.getElementById("mensaje");
    const contador = document.getElementById("contador");
    contador.textContent = `${textarea.value.length} / 400`;
}

function actualizarContaNombre() {
    const input = document.getElementById('nombre_evento');
    const contador = document.getElementById('contador_nombre');
    contador.textContent = `${input.value.length} / 100`;
}