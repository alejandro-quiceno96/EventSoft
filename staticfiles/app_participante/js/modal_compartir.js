function abrirCompartir(nombre, fechaInicio, fechaFin, enlace) {
    const url = urlDetalle.replace('/123', `/${enlace}`);
    const urlfull =  window.location.origin + url;
    const mensaje = `📢 ¡Te invito al evento "${nombre}"! 📅 Del ${fechaInicio} al ${fechaFin}. 🌐 Más información: ${urlfull}`;
    // Mostrar mensaje dentro del modal
    document.getElementById('mensajeEvento').innerText = mensaje;

    // Configurar enlace de WhatsApp
    document.getElementById('btnWhatsapp').href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;

    // Configurar enlace de Facebook
    document.getElementById('btnFacebook').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(enlace)}`;

    // Acción de copiar enlace
    document.getElementById('btnCopiar').onclick = function() {
        navigator.clipboard.writeText(urlfull).then(() => {
            alert("Enlace copiado al portapapeles ✅");
        }).catch(() => {
            alert("Error al copiar el enlace ❌");
        });
    };

    // Abrir modal
    let modal = new bootstrap.Modal(document.getElementById('modalCompartir'));
    modal.show();
}