document.addEventListener('DOMContentLoaded', function () {
    // Para admitir participantes directamente sin modal
    document.querySelectorAll('.btn-admitir').forEach(btn => {
        btn.addEventListener('click', function () {
            const participanteId = this.dataset.participanteId;
            const eventoId = this.dataset.eventoId;
            const urlTemplate = this.dataset.url;
            actualizarEstado(participanteId, eventoId, 'Admitido', urlTemplate);
        });
    });

    // Para abrir el modal de rechazo
    document.querySelectorAll('.btn-rechazar').forEach(btn => {
        btn.addEventListener('click', function () {
            const participanteId = this.dataset.participanteId;
            document.getElementById('participanteRechazoId').value = participanteId;
            const modalRechazo = new bootstrap.Modal(document.getElementById('modalRechazo'));
            modalRechazo.show();
        });
    });

    // Confirmar rechazo desde el modal
    const btnConfirmarRechazo = document.getElementById('btnRechazarConfirmacion');
    if (btnConfirmarRechazo) {
        btnConfirmarRechazo.addEventListener('click', function () {
            const participanteId = document.getElementById('participanteRechazoId').value;
            const eventoId = document.querySelector('input[name="evento_id"]').value;
            const urlTemplate = btnConfirmarRechazo.dataset.url;
            console.log(`Rechazando participante ${participanteId} para el evento ${eventoId}`);
            actualizarEstado(participanteId, eventoId, 'Rechazado', urlTemplate);
            // Cierra el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalRechazo'));
            if (modal) modal.hide();
        });
    }

    // Función para hacer POST a la URL correspondiente
    function actualizarEstado(participanteId, eventoId, nuevoEstado, urlTemplate) {
        const formData = new FormData();
        formData.append("evento_id", eventoId);
        console.log(`Actualizando estado de participante ${participanteId} a ${nuevoEstado}`);
        const finalUrl = urlTemplate
            .replace("/0/", `/${participanteId}/`)
            .replace("estado-placeholder", nuevoEstado);

        fetch(finalUrl, {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (res.ok) {
                location.reload();
            } else {
                throw new Error("Error en la solicitud");
            }
        })
        .catch(err => {
            console.error(err);
        });
    }
});
