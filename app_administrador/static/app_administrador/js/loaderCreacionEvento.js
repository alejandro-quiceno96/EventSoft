/**
 * loader.js
 * Activa el spinner del botón al hacer submit.
 * Compatible con formularios Django (CSRF incluido).
 */

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector(".boton-crear");
  if (!btn) return;

  // Envuelve el texto original para poder ocultarlo sin perder el icono
  wrapButtonContent(btn);

  // Escucha el submit del formulario padre
  const form = btn.closest("form");
  if (form) {
    form.addEventListener("submit", () => activateLoader(btn));
  } else {
    // Fallback: click directo si no hay form
    btn.addEventListener("click", () => activateLoader(btn));
  }
});

/**
 * Inserta el spinner y envuelve el label en un span
 * solo la primera vez (idempotente).
 */
function wrapButtonContent(btn) {
  if (btn.querySelector(".btn-spinner")) return; // ya inicializado

  // Envuelve todos los nodos hijos en .btn-label
  const label = document.createElement("span");
  label.className = "btn-label";
  label.style.display = "inline-flex";
  label.style.alignItems = "center";
  label.style.gap = "10px";

  while (btn.firstChild) {
    label.appendChild(btn.firstChild);
  }
  btn.appendChild(label);

  // Crea el spinner de tres puntos
  const spinner = document.createElement("div");
  spinner.className = "btn-spinner";
  spinner.innerHTML = "<span></span><span></span><span></span>";
  btn.appendChild(spinner);
}

/**
 * Activa el estado de carga en el botón.
 * @param {HTMLButtonElement} btn
 */
function activateLoader(btn) {
  btn.classList.add("is-loading");
  btn.disabled = true;
}

/**
 * Desactiva el loader manualmente si lo necesitas
 * (ej. tras un error de validación via fetch).
 * Uso: deactivateLoader(document.querySelector('.boton-crear'))
 * @param {HTMLButtonElement} btn
 */
function deactivateLoader(btn) {
  btn.classList.remove("is-loading");
  btn.disabled = false;
}