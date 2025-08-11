document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("formFichaTecnica");
  const modalSubir = new bootstrap.Modal(
    document.getElementById("modalSubirInfoTecnica")
  );
  const modalExito = new bootstrap.Modal(
    document.getElementById("modalExitoFicha")
  );

  document
    .getElementById("modalSubirInfoTecnica")
    .addEventListener("show.bs.modal", function (e) {
      const btn = e.relatedTarget;
      const eventoId = btn.getAttribute("data-evento-id");
      document.getElementById("eventoIdInput").value = eventoId;
    });

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const eventoId = document.getElementById("eventoIdInput").value;

    const formData = new FormData(form);
    const csrfToken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    ).value;
    const url = baseFichaTecnicaUrl.replace("123", eventoId);
    const response = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });

    if (response.ok) {
      modalSubir.hide();
      modalExito.show();
      form.reset();
    } else {
      alert("Hubo un error al subir el archivo.");
    }
  });
});
