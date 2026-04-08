(function () {
    const totalProyectos = document.querySelectorAll('.col-lg-4[data-nombre]').length;

    function actualizarContador(visibles) {
        const contador = document.getElementById('contadorProyectos');
        if (!contador) return;
        contador.textContent = visibles === totalProyectos
            ? `${totalProyectos} proyectos`
            : `${visibles} de ${totalProyectos}`;
    }

    window.filtrarProyectos = function () {
        const input = document.getElementById('buscadorProyectos');
        const termino = input.value.trim().toLowerCase();
        const cards = document.querySelectorAll('.col-lg-4[data-nombre]');
        const btnLimpiar = document.getElementById('btnLimpiar');
        const sinResultados = document.getElementById('sinResultados');

        btnLimpiar.style.display = termino.length > 0 ? 'flex' : 'none';

        let visibles = 0;

        cards.forEach(card => {
            const nombre = (card.dataset.nombre || '').toLowerCase();
            const codigo = (card.dataset.codigo || '').toLowerCase();
            const coincide = nombre.includes(termino) || codigo.includes(termino);
            card.classList.toggle('oculto', !coincide);
            if (coincide) visibles++;
        });

        sinResultados.style.display = visibles === 0 && termino.length > 0 ? 'block' : 'none';
        actualizarContador(visibles);
    };

    window.limpiarBuscador = function () {
        const input = document.getElementById('buscadorProyectos');
        input.value = '';
        input.focus();
        filtrarProyectos();
    };

    // Inicializar contador al cargar
    actualizarContador(totalProyectos);
})();

function showToast(msg) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-msg').textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }
 
  function actualizarCalificaciones() {
    const btn  = document.getElementById('btn-actualizar');
    const icon = document.getElementById('icon-actualizar');
 
    // Estado de carga visual
    btn.classList.add('loading');
    icon.classList.remove('fa-rotate');
    icon.classList.add('fa-spinner', 'fa-spin-custom');
    btn.lastChild.textContent = ' Actualizando...';
 
    // Recargar la página para obtener los datos reales del ranking
    setTimeout(() => {
        window.location.reload();
    }, 800);
  }
 
  // Helper para obtener el CSRF token de Django
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }