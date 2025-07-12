document.addEventListener('DOMContentLoaded', () => {
    const checkTodos = document.getElementById('check-todos');
    const parciales = document.querySelectorAll('.check-parcial');
    const formCorreo = document.getElementById('form-correo');
    const loader = document.getElementById('loader');

    const modalConfirmacion = document.getElementById('modalConfirmacionCorreo');
    const btnConfirmarEnvio = document.getElementById('btnConfirmarEnvioCorreo');

    // ✅ Checkbox "Todos" vs parciales
    checkTodos.addEventListener('change', function () {
        if (this.checked) {
            parciales.forEach(chk => {
                chk.checked = false;
                chk.disabled = true;
            });
        } else {
            parciales.forEach(chk => chk.disabled = false);
        }
    });

    // ✅ Máximo 2 parciales seleccionados
    parciales.forEach(chk => {
        chk.addEventListener('change', () => {
            const seleccionados = [...parciales].filter(c => c.checked).length;
            if (seleccionados >= 2) {
                parciales.forEach(c => {
                    if (!c.checked) c.disabled = true;
                });
            } else {
                parciales.forEach(c => c.disabled = false);
            }
        });
    });

    // ✅ Validación y apertura de modal de confirmación
    formCorreo.addEventListener('submit', function (e) {
        tinymce.triggerSave(); // 🔄 Sincronizar contenido del editor
        e.preventDefault();

        const contenido = document.getElementById('contenido');
        const checkboxes = document.querySelectorAll('input[name="destinatarios"]');
        const algunoMarcado = Array.from(checkboxes).some(cb => cb.checked);

        if (!algunoMarcado) {
            mostrarErrorCorreo("Debes seleccionar al menos un destinatario.");
            return;
        }

        if (!contenido.value.trim()) {
            mostrarErrorCorreo("El mensaje del correo no puede estar vacío.");
            return;
        }

        modalConfirmacion.classList.remove('hidden');
    });

    // ✅ Confirmar envío desde modal
    btnConfirmarEnvio.addEventListener('click', () => {
        cerrarModalConfirmacionCorreo();
        loader.classList.remove('hidden');
        formCorreo.submit();
    });
});


// 🔴 Mostrar error
function mostrarErrorCorreo(mensaje) {
    const modal = document.getElementById('modalErrorCorreo');
    const mensajeError = document.getElementById('mensajeErrorCorreo');
    mensajeError.textContent = mensaje;
    modal.classList.remove('hidden');
}

// 🔴 Cerrar error
function cerrarModalErrorCorreo() {
    document.getElementById('modalErrorCorreo').classList.add('hidden');
}

// 🟡 Cerrar confirmación
function cerrarModalConfirmacionCorreo() {
    document.getElementById('modalConfirmacionCorreo').classList.add('hidden');
}

// 🟢 Modal éxito (solo si backend lo activa con envio_exitoso)
function mostrarExitoCorreo() {
    const modal = document.getElementById('modalExitoCorreo');
    modal.classList.remove('hidden');
}
function cerrarModalExitoCorreo() {
    document.getElementById('modalExitoCorreo').classList.add('hidden');
}

function mostrarModalExito() {
    const modal = document.getElementById('modalExitoCorreo');
    modal.classList.remove('hidden');

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 1500);
}

