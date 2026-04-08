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