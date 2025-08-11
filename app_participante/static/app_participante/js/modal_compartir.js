function abrirCompartir(nombre, fechaInicio, fechaFin, enlace) {
    const mensaje = `📢 ¡Te invito al evento "${nombre}"! 📅 Del ${fechaInicio} al ${fechaFin}. 🌐 Más información: ${enlace}`;
    
    // Mostrar mensaje dentro del modal
    document.getElementById('mensajeEvento').innerText = mensaje;

    // Configurar enlace de WhatsApp
    document.getElementById('btnWhatsapp').href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;

    // Configurar enlace de Facebook
    document.getElementById('btnFacebook').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(enlace)}`;

    // Acción de copiar enlace
    document.getElementById('btnCopiar').onclick = function() {
        navigator.clipboard.writeText(enlace).then(() => {
            alert("Enlace copiado al portapapeles ✅");
        }).catch(() => {
            alert("Error al copiar el enlace ❌");
        });
    };

    // Abrir modal
    let modal = new bootstrap.Modal(document.getElementById('modalCompartir'));
    modal.show();
}