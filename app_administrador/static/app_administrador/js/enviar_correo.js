document.addEventListener('DOMContentLoaded', () => {
    const checkTodos = document.getElementById('check-todos');
    const checkboxesRol = document.querySelectorAll('input[name="destinatarios"]:not(#check-todos)');
    const formCorreo = document.getElementById('form-correo');
    const loader = document.getElementById('loader');
    const modalConfirmacion = document.getElementById('modalConfirmacionCorreo');
    const btnConfirmarEnvio = document.getElementById('btnConfirmarEnvioCorreo');

    // ✅ Mostrar u ocultar tablas por cada checkbox de rol
    checkboxesRol.forEach(chk => {
        chk.addEventListener('change', () => {
            const tablaId = `tabla-${chk.value}`;
            const tabla = document.getElementById(tablaId);
            if (!tabla) return;

            if (chk.checked) {
                tabla.classList.remove('oculto');
            } else {
                tabla.classList.add('oculto');
                tabla.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
        });
    });

    // ✅ Control del checkbox "Todos"
    checkTodos.addEventListener('change', function () {
        if (this.checked) {
            checkboxesRol.forEach(chk => {
                chk.checked = false;
                chk.disabled = true;

                // Ocultar sublistas y desmarcar
                const tabla = document.getElementById(`tabla-${chk.value}`);
                if (tabla) {
                    tabla.classList.add('oculto');
                    tabla.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
                }
            });
        } else {
            checkboxesRol.forEach(chk => {
                chk.disabled = false;
            });
        }
    });

    // ✅ Validación al enviar
    formCorreo.addEventListener('submit', function (e) {
        tinymce.triggerSave(); // Actualiza el contenido del editor TinyMCE
        e.preventDefault();

        const contenido = document.getElementById('contenido').value.trim();
        const algunoMarcado = checkTodos.checked || Array.from(checkboxesRol).some(cb => cb.checked);

        if (!algunoMarcado) {
            mostrarErrorCorreo("Debes seleccionar al menos un destinatario.");
            return;
        }

        // Si se seleccionan roles individuales, asegurarse de que tengan seleccionados
        if (!checkTodos.checked) {
            for (let chk of checkboxesRol) {
                if (chk.checked) {
                    const seleccionados = document.querySelectorAll(`#tabla-${chk.value} input[name="${chk.value}_seleccionados"]:checked`);
                    if (seleccionados.length === 0) {
                        mostrarErrorCorreo(`Debes seleccionar al menos un ${chk.value.slice(0, -1)}.`);
                        return;
                    }
                }
            }
        }

        if (!contenido) {
            mostrarErrorCorreo("El mensaje del correo no puede estar vacío.");
            return;
        }

        modalConfirmacion.classList.remove('hidden');
    });

    // ✅ Confirmación final
    btnConfirmarEnvio.addEventListener('click', () => {
        cerrarModalConfirmacionCorreo();
        loader.classList.remove('hidden');
        formCorreo.submit();
    });

    // ✅ Inicializar paginación si existen las tablas
    ['asistentes', 'participantes', 'evaluadores'].forEach(rol => {
        const tablaId = `tabla-${rol}-lista`;
        const paginacionId = `paginacion-${rol}`;
        const nombreCheckbox = `${rol}_seleccionados`;

        if (document.getElementById(tablaId)) {
            paginarTabla(tablaId, paginacionId, nombreCheckbox);
        }
    });
});

// 🔴 Modal de error
function mostrarErrorCorreo(mensaje) {
    document.getElementById('mensajeErrorCorreo').textContent = mensaje;
    document.getElementById('modalErrorCorreo').classList.remove('hidden');
}
function cerrarModalErrorCorreo() {
    document.getElementById('modalErrorCorreo').classList.add('hidden');
}

// 🟡 Modal de confirmación
function cerrarModalConfirmacionCorreo() {
    document.getElementById('modalConfirmacionCorreo').classList.add('hidden');
}

// 🟢 Modal de éxito
function mostrarModalExito() {
    const modal = document.getElementById('modalExitoCorreo');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('hidden'), 1500);
}

// ✅ Seleccionar todos en tabla
function seleccionarTodos(masterCheckbox, name) {
    const checkboxes = document.querySelectorAll(`input[name="${name}"]`);
    checkboxes.forEach(cb => cb.checked = masterCheckbox.checked);
}

// ✅ Paginación
function paginarTabla(tablaId, contenedorId, nombreCheckbox, filasPorPagina = 10) {
    const tabla = document.getElementById(tablaId);
    const cuerpo = tabla.querySelector('tbody');
    const filas = Array.from(cuerpo.querySelectorAll('tr'));
    const paginacion = document.getElementById(contenedorId);
    let paginaActual = 1;
    const totalPaginas = Math.ceil(filas.length / filasPorPagina);
    const seleccionados = new Set();

    cuerpo.querySelectorAll(`input[name="${nombreCheckbox}"]:checked`).forEach(cb => {
        seleccionados.add(cb.value);
    });

    function renderizarPagina(pagina) {
        cuerpo.innerHTML = '';
        const inicio = (pagina - 1) * filasPorPagina;
        const fin = inicio + filasPorPagina;
        filas.slice(inicio, fin).forEach(fila => {
            const input = fila.querySelector(`input[name="${nombreCheckbox}"]`);
            input.checked = seleccionados.has(input.value);
            input.addEventListener('change', () => {
                if (input.checked) {
                    seleccionados.add(input.value);
                } else {
                    seleccionados.delete(input.value);
                }
            });
            cuerpo.appendChild(fila);
        });
        paginaActual = pagina;
        renderizarControles();
    }

    function renderizarControles() {
        paginacion.innerHTML = '';
        if (totalPaginas <= 1) return;

        const btnPrev = document.createElement('button');
        btnPrev.textContent = '← Anterior';
        btnPrev.disabled = paginaActual === 1;
        btnPrev.onclick = () => renderizarPagina(paginaActual - 1);
        paginacion.appendChild(btnPrev);

        const texto = document.createElement('span');
        texto.textContent = ` Página ${paginaActual} de ${totalPaginas} `;
        paginacion.appendChild(texto);

        const btnNext = document.createElement('button');
        btnNext.textContent = 'Siguiente →';
        btnNext.disabled = paginaActual === totalPaginas;
        btnNext.onclick = () => renderizarPagina(paginaActual + 1);
        paginacion.appendChild(btnNext);
    }

    renderizarPagina(1);
}
