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

            const estaEditando = !descripcion.readOnly;

            if (estaEditando) {
                // GUARDAR cambios: enviar POST a una URL
                const url = btn.getAttribute("data-url");
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                const nuevoPorcentaje = parseFloat(porcentaje.value);

                if (isNaN(nuevoPorcentaje) || nuevoPorcentaje < 0 || nuevoPorcentaje > 100) {
                    alert("Porcentaje inválido. Debe ser un número entre 0 y 100.");
                    return;
                }

                // Validar que la suma total no supere 100
                let suma = 0;
                document.querySelectorAll('.porcentaje-existente').forEach(input => {
                    const valor = parseFloat(input.value);
                    const id = input.dataset.id;

                    if (!isNaN(valor)) {
                        if (id === criterioId) {
                            suma += nuevoPorcentaje;
                        } else {
                            suma += valor;
                        }
                    }
                });

                if (suma > 100) {
                    alert(`Error: La suma total de los porcentajes supera 100%. Actualmente: ${suma.toFixed(2)}%.`);
                    return;
                }

                const data = {
                    descripcion: descripcion.value,
                    porcentaje: nuevoPorcentaje
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
                        descripcion.readOnly = true;
                        porcentaje.readOnly = true;
                        actualizarTotalPorcentaje();
                        mostrarModalExito("Criterio Modificado correctamente");
                    } else {
                        alert('Error al actualizar el criterio');
                    }
                } catch (error) {
                    alert('Error de red al guardar');
                    console.error(error);
                }
            } else {
                // Cambiar a modo edición
                descripcion.readOnly = false;
                porcentaje.readOnly = false;
                btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Guardar cambios';
            }
        });
    });

    // Eliminar criterio
    document.querySelectorAll('.btn-eliminar-criterios').forEach(btn => {
        btn.addEventListener('click', function () {
            criterioAEliminar = this.getAttribute('data-id');
            urlFinal = this.getAttribute('data-url');
            cardColEliminar = this.closest('.col-md-6, .col-lg-4');

            const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminar'));
            modal.show();
        });
    });

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
        }, 1500);
    }

    const formAgregar = document.getElementById("form-criterios");
    formAgregar?.addEventListener("submit", function (e) {
        const nuevoPorcentaje = parseFloat(this.querySelector('input[name="porcentaje[]"]').value);
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

    actualizarTotalPorcentaje();
});
