document.addEventListener("DOMContentLoaded", () => {

  // Botón Modificar/Guardar
  document.querySelectorAll(".btn-modificar").forEach(btn => {
      btn.addEventListener("click", function () {
          const row = this.closest("tr");
          const inputs = row.querySelectorAll("input");
          const isDisabled = inputs[0].disabled;
          if (isDisabled) {
              inputs.forEach(input => input.disabled = false);
              this.textContent = "Guardar";
          } else {
              const id = row.getAttribute("data-id");
              const descripcion = inputs[0].value;
              const peso = inputs[1].value;

              fetch(`/criterios_evaluacion/modificar/${id}`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ descripcion, peso })
              }).then(res => {
                  if (res.ok) {
                      alert("Criterio actualizado");
                      inputs.forEach(input => input.disabled = true);
                      this.textContent = "Modificar";
                      location.reload(); // Refrescar
                  }
              });
          }
      });
  });

  // Botón Eliminar con shake
  document.querySelectorAll(".btn-eliminar").forEach(btn => {
      btn.addEventListener("click", function () {
          const row = this.closest("tr");
          const id = row.getAttribute("data-id");

          // Agregar animación Shake al botón
          this.classList.add('shake');
          setTimeout(() => {
              this.classList.remove('shake');
          }, 400);

          if (confirm("¿Seguro que deseas eliminar este criterio?")) {
              fetch(`/criterios_evaluacion/eliminar/${id}`, {
                  method: "POST"
              }).then(res => {
                  if (res.ok) {
                      row.remove();
                      location.reload(); // Refrescar
                  }
              });
          }
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

  actualizarTotalPorcentaje(); // Llamar una vez al inicio

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

});
