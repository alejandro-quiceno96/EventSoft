document.addEventListener('DOMContentLoaded', function () {
    const modalAdmitir = document.getElementById('modalAdmitir');
    const modalRechazo = document.getElementById('modalRechazo');

    let asistenteId = null;
    let eventoId = null;
    let urlBase = null;

    // Abrir modal admitir
    document.querySelectorAll('.btn-admitir').forEach(button => {
        button.addEventListener('click', function () {
            asistenteId = this.dataset.id;
            eventoId = this.dataset.evento;
            urlBase = this.dataset.url;

            document.getElementById('mensaje-admitir').innerText = `¿Estás seguro que deseas admitir a ${this.dataset.nombre}?`;
        });
    });

    // Confirmar admitir
    document.getElementById('confirmarAdmitir').addEventListener('click', function () {
        const url = urlBase.replace('0', asistenteId).replace('estado-placeholder', 'Admitido');

        const formData = new FormData();
        formData.append('evento_id', eventoId);

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        }).then(data => {
            if (data?.status === 'error') {
                alert(data.message);
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    });

    // Abrir modal rechazo
    document.querySelectorAll('.btn-rechazar').forEach(button => {
        button.addEventListener('click', function () {
            asistenteId = this.dataset.id;
            eventoId = this.dataset.evento;
            urlBase = this.dataset.url;

            document.getElementById('mensaje-rechazo').innerText = `¿Estás seguro que deseas rechazar a ${this.dataset.nombre}?`;
        });
    });

    // Confirmar rechazo
    document.getElementById('confirmarRechazo').addEventListener('click', function () {
        const url = urlBase.replace('0', asistenteId).replace('estado-placeholder', 'Rechazado');

        const formData = new FormData();
        formData.append('evento_id', eventoId);

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        }).then(data => {
            if (data?.status === 'error') {
                alert(data.message);
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    });
});

// Función para obtener CSRF desde las cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
