document.addEventListener('DOMContentLoaded', () => {
    const checkTodos = document.getElementById('check-todos');
    const parciales = document.querySelectorAll('.check-parcial');
    const formCorreo = document.getElementById('form-correo');
    const loader = document.getElementById('loader');

    const modalConfirmacion = document.getElementById('modalConfirmacionCorreo');
    const btnConfirmarEnvio = document.getElementById('btnConfirmarEnvioCorreo');

    // ✅ Manejo de sublistas (asistentes, participantes, evaluadores)
    const checkAsistentes = document.querySelector('input[value="asistentes"]');
    const sublistaAsistentes = document.getElementById('lista-asistentes');
    
    const checkParticipantes = document.querySelector('input[value="participantes"]');
    const sublistaParticipantes = document.getElementById('lista-participantes');
    
    const checkEvaluadores = document.querySelector('input[value="evaluadores"]');
    const sublistaEvaluadores = document.getElementById('lista-evaluadores');

    // 🔍 DEBUG: Verificar si los elementos existen
    console.log('Elementos encontrados:');
    console.log('checkAsistentes:', checkAsistentes);
    console.log('sublistaAsistentes:', sublistaAsistentes);
    console.log('checkParticipantes:', checkParticipantes);
    console.log('sublistaParticipantes:', sublistaParticipantes);
    console.log('checkEvaluadores:', checkEvaluadores);
    console.log('sublistaEvaluadores:', sublistaEvaluadores);

    // ✅ Checkbox "Todos" vs parciales
    checkTodos.addEventListener('change', function () {
        console.log('Checkbox "Todos" cambiado:', this.checked);
        if (this.checked) {
            parciales.forEach(chk => {
                chk.checked = false;
                chk.disabled = true;
            });
            // Ocultar todas las sublistas cuando "Todos" está seleccionado
            ocultarTodasLasSublistas();
        } else {
            parciales.forEach(chk => chk.disabled = false);
        }
    });

    // ✅ Función para ocultar todas las sublistas y deseleccionar checkboxes
    function ocultarTodasLasSublistas() {
        console.log('Ocultando todas las sublistas...');
        if (sublistaAsistentes) {
            sublistaAsistentes.classList.add('oculto');
            sublistaAsistentes.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
        if (sublistaParticipantes) {
            sublistaParticipantes.classList.add('oculto');
            sublistaParticipantes.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
        if (sublistaEvaluadores) {
            sublistaEvaluadores.classList.add('oculto');
            sublistaEvaluadores.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
    }

    // ✅ Máximo 2 parciales seleccionados (si quieres mantener esta restricción)
    parciales.forEach(chk => {
        chk.addEventListener('change', () => {
            const seleccionados = [...parciales].filter(c => c.checked).length;
            console.log('Parciales seleccionados:', seleccionados);
            if (seleccionados >= 2) {
                parciales.forEach(c => {
                    if (!c.checked) c.disabled = true;
                });
            } else {
                parciales.forEach(c => c.disabled = false);
            }
        });
    });

    // ✅ Mostrar/ocultar lista de asistentes
    if (checkAsistentes && sublistaAsistentes) {
        checkAsistentes.addEventListener('change', function () {
            console.log('Checkbox asistentes cambiado:', this.checked);
            if (this.checked) {
                sublistaAsistentes.classList.remove('oculto');
                console.log('Mostrando lista de asistentes');
            } else {
                sublistaAsistentes.classList.add('oculto');
                console.log('Ocultando lista de asistentes');
                // Deseleccionar todos los asistentes si se oculta
                sublistaAsistentes.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
        });
    } else {
        console.log('ERROR: No se encontraron elementos de asistentes');
    }

    // ✅ Mostrar/ocultar lista de participantes
    if (checkParticipantes && sublistaParticipantes) {
        checkParticipantes.addEventListener('change', function () {
            console.log('Checkbox participantes cambiado:', this.checked);
            if (this.checked) {
                sublistaParticipantes.classList.remove('oculto');
                console.log('Mostrando lista de participantes');
            } else {
                sublistaParticipantes.classList.add('oculto');
                console.log('Ocultando lista de participantes');
                // Deseleccionar todos los participantes si se oculta
                sublistaParticipantes.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
        });
    } else {
        console.log('ERROR: No se encontraron elementos de participantes');
        console.log('checkParticipantes existe:', !!checkParticipantes);
        console.log('sublistaParticipantes existe:', !!sublistaParticipantes);
    }

    // ✅ Mostrar/ocultar lista de evaluadores
    if (checkEvaluadores && sublistaEvaluadores) {
        checkEvaluadores.addEventListener('change', function () {
            console.log('Checkbox evaluadores cambiado:', this.checked);
            if (this.checked) {
                sublistaEvaluadores.classList.remove('oculto');
                console.log('Mostrando lista de evaluadores');
            } else {
                sublistaEvaluadores.classList.add('oculto');
                console.log('Ocultando lista de evaluadores');
                // Deseleccionar todos los evaluadores si se oculta
                sublistaEvaluadores.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
        });
    } else {
        console.log('ERROR: No se encontraron elementos de evaluadores');
        console.log('checkEvaluadores existe:', !!checkEvaluadores);
        console.log('sublistaEvaluadores existe:', !!sublistaEvaluadores);
    }

    // 🔍 DEBUG: Verificar HTML actual
    console.log('HTML del formulario:');
    console.log(document.querySelector('.checkbox-group')?.innerHTML);

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

        // Validar que si se seleccionó "asistentes", al menos uno esté marcado
        if (checkAsistentes && checkAsistentes.checked) {
            const asistentesSeleccionados = sublistaAsistentes.querySelectorAll('input[name="asistentes_seleccionados"]:checked');
            if (asistentesSeleccionados.length === 0) {
                mostrarErrorCorreo("Debes seleccionar al menos un asistente.");
                return;
            }
        }

        // Validar que si se seleccionó "participantes", al menos uno esté marcado
        if (checkParticipantes && checkParticipantes.checked) {
            const participantesSeleccionados = sublistaParticipantes.querySelectorAll('input[name="participantes_seleccionados"]:checked');
            if (participantesSeleccionados.length === 0) {
                mostrarErrorCorreo("Debes seleccionar al menos un participante.");
                return;
            }
        }

        // Validar que si se seleccionó "evaluadores", al menos uno esté marcado
        if (checkEvaluadores && checkEvaluadores.checked) {
            const evaluadoresSeleccionados = sublistaEvaluadores.querySelectorAll('input[name="evaluadores_seleccionados"]:checked');
            if (evaluadoresSeleccionados.length === 0) {
                mostrarErrorCorreo("Debes seleccionar al menos un evaluador.");
                return;
            }
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

// 🟢 Modal éxito
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