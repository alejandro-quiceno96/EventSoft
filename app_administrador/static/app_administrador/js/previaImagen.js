document.getElementById("imagen_evento").addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById("previewImagen").src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('documento_evento').addEventListener('change', function(event) {
    const file = event.target.files[0]; // Obtener el archivo seleccionado

    if (file && file.type === "application/pdf") {
        const fileURL = URL.createObjectURL(file); // Crear una URL temporal del archivo
        const previewFrame = document.getElementById('previewDocumento');

        previewFrame.src = fileURL;  // Asignar la URL al `iframe`
        previewFrame.style.display = "block";  // Mostrar el `iframe`
    } else {
        alert("Por favor, selecciona un archivo PDF válido.");
    }
});