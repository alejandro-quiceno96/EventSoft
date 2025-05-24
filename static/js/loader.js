const loader = document.getElementById('loader');
const loaderMsg = document.getElementById('loader-message');

function showLoader(message = "Cargando...") {
    loaderMsg.textContent = message;
    loader.style.display = "flex";
    loader.style.opacity = "1";
}

function hideLoader() {
    loader.style.opacity = "0";
    setTimeout(() => loader.style.display = "none", 500);
}

// Al cargar la página
window.addEventListener('load', function () {
    if (navigator.onLine) {
        hideLoader();
    } else {
        showLoader("Esperando conexión...");
    }
});

// Si se pierde conexión
window.addEventListener('offline', function () {
    showLoader("Esperando conexión...");
});

// Si vuelve la conexión
window.addEventListener('online', function () {
    hideLoader();
});