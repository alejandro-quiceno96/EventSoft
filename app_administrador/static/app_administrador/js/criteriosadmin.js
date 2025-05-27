document.addEventListener("DOMContentLoaded", () => {
    let criterioAEliminar = null;
    let urlFinal = null;
    let cardColEliminar = null;
  // Botón Modificar/Guardar
    document.querySelectorAll('.btn-modificar-criterios').forEach(btn => {
        btn.addEventListener('click', async function () {
            const card = btn.closest('.card');
            const descripcion = card.querySelector('.descripcion');
            const porcentaje = card.querySelector('.porcentaje-existente');
            const criterioId = porcentaje.dataset.id;

            const estaEditando = !descripcion.disabled;

            if (estaEditando) {
                // GUARDAR cambios: enviar POST a una URL
                const url = btn.getAttribute("data-url");
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                const data = {
                    descripcion: descripcion.value,
                    porcentaje: porcentaje.value
                };

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrftoken
                        },
                        body: JSON.stringify(data)
                    });

                    if (response.ok) {
                        btn.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Modificar';
                        descripcion.disabled = true;
                        porcentaje.disabled = true;
                        actualizarTotalPorcentaje();
                        mostrarModalExito("Criterio Modificado correctamente"); // Mostrar modal de éxito
                    } else {
                        alert('Error al actualizar el criterio');
                    }
                } catch (error) {
                    alert('Error de red al guardar');
                    console.error(error);
                }
            } else {
                // Cambiar a modo edición
                descripcion.disabled = false;
                porcentaje.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Guardar cambios';
            }
        });
    });



    // Al hacer clic en el botón de eliminar
    document.querySelectorAll('.btn-eliminar-criterios').forEach(btn => {
        btn.addEventListener('click', function () {
            criterioAEliminar = this.getAttribute('data-id');
            urlEliminar = this.getAttribute('data-url');
            urlFinal = urlEliminar
            cardColEliminar = this.closest('.col-md-6, .col-lg-4');

            // Mostrar el modal
            const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminar'));
            modal.show();
        });
    });

    // Al confirmar eliminación desde el modal
    document.getElementById('btnConfirmarEliminar').addEventListener('click', function () {
        fetch(urlFinal, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        })
        .then(response => {
            if (response.ok) {
                cardColEliminar.classList.add('card-eliminada');
                setTimeout(() => {
                    cardColEliminar.remove();
                    mostrarModalExito("Criterio eliminado correctamente");
                    actualizarTotalPorcentaje();
                }, 300);

                const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarEliminar'));
                modal.hide();
            } else {
                alert("Error al eliminar el criterio.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Error al eliminar el criterio.");
        });
    });



  // Función para actualizar el porcentaje total
    function actualizarTotalPorcentaje() {
      let total = 0;
      document.querySelectorAll('.porcentaje-existente').forEach(input => {
          const valor = parseFloat(input.value);
          if (!isNaN(valor)) {
              total += valor;
          }
      });
      document.getElementById("porcentaje-total").textContent = total.toFixed(2);
    } 

    function mostrarModalExito(mensaje) {
        const modal = new bootstrap.Modal(document.getElementById('modalExito'));
        document.querySelector("#modalExito .modal-body").innerText = mensaje;
        modal.show();
        setTimeout(() => {
            modal.hide();
        }, 1500); // Ocultar después de 2 segundos
    }




  // Validar porcentaje al agregar nuevo criterio
  const formAgregar = document.getElementById("form-criterios"); // Corregido el id
  formAgregar?.addEventListener("submit", function (e) {
      const nuevoPorcentaje = parseFloat(this.querySelector('input[name="porcentaje"]').value);
      const inputsExistentes = document.querySelectorAll(".porcentaje-existente");
      
      let sumaExistente = 0;
      inputsExistentes.forEach(input => {
          const val = parseFloat(input.value);
          if (!isNaN(val)) sumaExistente += val;
      });

      if (isNaN(nuevoPorcentaje)) {
          alert("Por favor ingresa un porcentaje válido.");
          e.preventDefault();
          return;
      }

      if ((sumaExistente + nuevoPorcentaje) > 100) {
          alert(`Error: La suma total de los porcentajes supera 100%. Actualmente: ${sumaExistente}%.`);
          e.preventDefault();
      }
  });

actualizarTotalPorcentaje()
});
