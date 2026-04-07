// Seleccionar todos los botones de dropdown
const dropdownBtns = document.querySelectorAll('.dropdown-btn');

// Función para manejar la apertura y cierre de los dropdowns
dropdownBtns.forEach(function(btn) {
    btn.addEventListener('click', function(event) {
        // Evitar que se cierre inmediatamente si ya está abierto
        event.stopPropagation();

        // Cerrar otros dropdowns antes de abrir el nuevo
        dropdownBtns.forEach(function(otherBtn) {
            if (otherBtn !== btn) {
                otherBtn.classList.remove('active');
                otherBtn.nextElementSibling.style.display = 'none';
            }
        });

        // Si el dropdown está cerrado, abrirlo
        const dropdown = this.nextElementSibling;
        if (this.classList.contains('active')) {
            this.classList.remove('active');
            dropdown.style.display = 'none';
        } else {
            this.classList.add('active');
            dropdown.style.display = 'block';
        }
    });
});

// Cuando el sidebar se cierre, cerramos todos los dropdowns
const sidebar = document.querySelector('.sidebar');
sidebar.addEventListener('transitionend', function() {
    if (sidebar.style.width === '80px') { // Si el sidebar está cerrado
        dropdownBtns.forEach(function(btn) {
            btn.classList.remove('active');
            btn.nextElementSibling.style.display = 'none';
        });
    }
});

// Cerrar todos los dropdowns si se hace clic fuera del sidebar
document.addEventListener('click', function(event) {
    const isSidebarClick = sidebar.contains(event.target);
    if (!isSidebarClick) {
        dropdownBtns.forEach(function(btn) {
            btn.classList.remove('active');
            btn.nextElementSibling.style.display = 'none';
        });
    }
});
