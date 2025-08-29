
let paginaActual = 1;
const totalPaginas = 2;
const tipoEvento = document.getElementById("tipo_evento");
const campoParticipacion = document.getElementById("campo-participacion");
const tipoParticipacion = document.getElementById("tipo_participacion");
const campoMaximo = document.getElementById("campo-maximo");
const maxIntegrantes = document.getElementById("max_integrantes");

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    inicializarFormulario();
    configurarValidaciones();
    configurarCargaArchivos();
    actualizarProgreso();
    
    // Configuración inicial del toggle de participantes
    document.getElementById("permitir_participantes").value = "0";
    toggleCantidadParticipantes();
});

// ===== FUNCIONES DE NAVEGACIÓN (TU CÓDIGO ORIGINAL MEJORADO) =====
function siguiente(pagina) {
    console.log(`Intentando pasar a la página ${pagina}`);

    // Obtener la página activa actual
    let paginaActual = document.querySelector(".pagina-activa");

    // Obtener todos los inputs, textareas y selects dentro de la página actual
    let inputs = paginaActual.querySelectorAll("input, textarea, select");

    // Verificar validación de fechas si estamos en la página 1
    if (pagina === 2 && !validarFecha()) {
        return;
    }

    // Verificar si hay algún campo vacío
    for (let input of inputs) {
        if (input.hasAttribute("required")) {
            let isEmpty = false;

            // Para inputs normales y textareas
            if (input.type === "text" || input.tagName === "TEXTAREA" || input.type === "date") {
                isEmpty = input.value.trim() === "";
            }

            // Para datetime-local, usar valueAsDate
            if (input.type === "datetime-local") {
                isEmpty = !input.value;
            }

            // Para selects, verificar que haya sido seleccionado un valor válido
            if (input.tagName === "SELECT") {
                isEmpty = input.value === "" || input.value === null;
            }

            // Para inputs de archivo
            if (input.type === "file") {
                isEmpty = !input.files || input.files.length === 0;
            }

            if (isEmpty) {
                // Mejorar la experiencia del usuario
                mostrarError(input, "Este campo es obligatorio");
                input.focus();
                return;
            } else {
                // Remover error si el campo ahora es válido
                removerError(input);
            }
        }
    }

    // Si todos los campos están llenos, cambiar de página
    paginaActual.classList.remove("pagina-activa");
    paginaActual.classList.add("pagina-inactiva");

    let nuevaPagina = document.getElementById("pagina" + pagina);
    nuevaPagina.classList.remove("pagina-inactiva");
    nuevaPagina.classList.add("pagina-activa");

    // Actualizar progreso y página actual
    window.paginaActual = pagina;
    actualizarProgreso();
    
    // Scroll al inicio
    window.scrollTo({ top: 0, behavior: 'smooth' });

    console.log(`Cambio a la página ${pagina} exitosamente`);
}

function volver(pagina) {
    console.log(`Volviendo a la página ${pagina}`);

    // Obtener la página activa actual
    let paginaActual = document.querySelector(".pagina-activa");

    // Cambiar la clase para ocultar la página actual
    paginaActual.classList.remove("pagina-activa");
    paginaActual.classList.add("pagina-inactiva");

    // Mostrar la página anterior
    let paginaAnterior = document.getElementById("pagina" + pagina);
    paginaAnterior.classList.remove("pagina-inactiva");
    paginaAnterior.classList.add("pagina-activa");

    // Actualizar progreso y página actual
    window.paginaActual = pagina;
    actualizarProgreso();
    
    // Scroll al inicio
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ===== BARRA DE PROGRESO =====
function actualizarProgreso() {
    const progreso = document.getElementById('progreso-fill');
    const paso1 = document.getElementById('paso-1');
    const paso2 = document.getElementById('paso-2');
    
    if (!progreso || !paso1 || !paso2) return;
    
    if (window.paginaActual === 1) {
        progreso.style.width = '50%';
        paso1.classList.add('active');
        paso1.classList.remove('completed');
        paso2.classList.remove('active');
    } else if (window.paginaActual === 2) {
        progreso.style.width = '100%';
        paso1.classList.add('completed');
        paso1.classList.remove('active');
        paso2.classList.add('active');
    }
}

// ===== CONTADORES DE CARACTERES (TU CÓDIGO ORIGINAL) =====
function actualizarContador() {
    const textarea = document.getElementById("descripcion_evento");
    const contador = document.getElementById("contador");
    
    if (textarea && contador) {
        const actual = textarea.value.length;
        const maximo = 400;
        contador.textContent = `${actual} / ${maximo}`;
        
        // Cambiar color según proximidad al límite
        contador.classList.remove('warning', 'danger');
        if (actual > maximo * 0.8) {
            contador.classList.add('warning');
        }
        if (actual >= maximo) {
            contador.classList.add('danger');
        }
    }
}

function actualizarContaNombre() {
    const input = document.getElementById('nombre_evento');
    const contador = document.getElementById('contador_nombre');
    
    if (input && contador) {
        const actual = input.value.length;
        const maximo = 100;
        contador.textContent = `${actual} / ${maximo}`;
        
        // Cambiar color según proximidad al límite
        contador.classList.remove('warning', 'danger');
        if (actual > maximo * 0.8) {
            contador.classList.add('warning');
        }
        if (actual >= maximo) {
            contador.classList.add('danger');
        }
    }
}

// ===== MANEJO DE CUPO DE PARTICIPANTES (TU CÓDIGO ORIGINAL MEJORADO) =====
function toggleCantidadParticipantes() {
    const select = document.getElementById('permitir_participantes');
    const cantidadDiv = document.getElementById('cantidad_participantes_div');
    const input = document.getElementById('cantidad_personas');

    if (select && cantidadDiv && input) {
        if (select.value === '1') {
            cantidadDiv.style.display = 'block';
            input.required = true;
            // Animación de aparición
            cantidadDiv.style.opacity = '0';
            cantidadDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                cantidadDiv.style.transition = 'all 0.3s ease';
                cantidadDiv.style.opacity = '1';
                cantidadDiv.style.transform = 'translateY(0)';
            }, 10);
        } else {
            cantidadDiv.style.display = 'none';
            input.required = false;
            input.value = '1';
        }
    }
}

// ===== VALIDACIÓN DE FECHAS (TU CÓDIGO ORIGINAL) =====
function validarFecha() {
    const fechaInicio = document.getElementById("fecha_inicio").value;
    const fechaFin = document.getElementById("fecha_fin").value;

    if (fechaInicio && fechaFin) {
        const inicio = new Date(fechaInicio);
        const fin = new Date(fechaFin);
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0); // Resetear la hora para comparar solo fechas

        // Validar que las fechas no sean en el pasado
        if (inicio < hoy) {
            mostrarError(document.getElementById("fecha_inicio"), "La fecha de inicio no puede ser en el pasado");
            return false;
        }

        if (fin < hoy) {
            mostrarError(document.getElementById("fecha_fin"), "La fecha de fin no puede ser en el pasado");
            return false;
        }

        // Validar que fecha de inicio no sea posterior a fecha de fin
        if (inicio > fin) {
            mostrarError(document.getElementById("fecha_fin"), "La fecha de inicio no puede ser posterior a la fecha de fin");
            return false;
        }

        // Si todo está bien, remover errores
        removerError(document.getElementById("fecha_inicio"));
        removerError(document.getElementById("fecha_fin"));
    }
    return true;
}

// ===== MANEJO DE CATEGORÍAS DINÁMICAS (TU CÓDIGO ORIGINAL MEJORADO) =====
function inicializarFormulario() {
    const areaSelect = document.getElementById('area');
    const categoriaSelect = document.getElementById('categoria');
    
    if (areaSelect && categoriaSelect) {
        areaSelect.addEventListener('change', function() {
            cargarCategorias(this.value);
        });
    }
}

// Evento para cargar categorías (tu código original)
document.addEventListener('DOMContentLoaded', function() {
    const areaSelect = document.getElementById("area");
    if (areaSelect) {
        areaSelect.addEventListener("change", function () {
            let areaId = this.value;
            let categoriaSelect = document.getElementById("categoria");
            categoriaSelect.innerHTML = '<option value="">Selecciona una categoría</option>';

            if (areaId) {
                // Mostrar loading
                categoriaSelect.innerHTML = '<option value="">Cargando categorías...</option>';
                
                let url = baseCategoriaUrl + areaId;

                fetch(url)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Error en la respuesta del servidor');
                        }
                        return response.json();
                    })
                    .then(data => {
                        categoriaSelect.innerHTML = '<option value="">Selecciona una categoría</option>';
                        data.forEach(categoria => {
                            let option = new Option(categoria.cat_nombre, categoria.cat_codigo);
                            categoriaSelect.add(option);
                        });
                    })
                    .catch(error => {
                        console.error('Error al cargar categorías:', error);
                        categoriaSelect.innerHTML = '<option value="">Error al cargar categorías</option>';
                        mostrarError(categoriaSelect, 'Error al cargar las categorías. Intenta nuevamente.');
                    });
            }
        });
    }
});

// ===== SISTEMA DE VALIDACIÓN Y ERRORES =====
function mostrarError(campo, mensaje) {
    // Remover error anterior si existe
    removerError(campo);
    
    // Agregar clase de error
    campo.classList.add('campo-error');
    
    // Crear elemento de mensaje
    const mensajeError = document.createElement('div');
    mensajeError.className = 'mensaje-error';
    mensajeError.textContent = mensaje;
    mensajeError.setAttribute('data-error-for', campo.id);
    
    // Insertar después del campo
    campo.parentNode.insertBefore(mensajeError, campo.nextSibling);
}

function removerError(campo) {
    // Remover clase de error
    campo.classList.remove('campo-error');
    
    // Remover mensaje de error
    const mensajeError = campo.parentNode.querySelector(`[data-error-for="${campo.id}"]`);
    if (mensajeError) {
        mensajeError.remove();
    }
}

function mostrarExito(campo, mensaje) {
    campo.classList.add('campo-exito');
    
    const mensajeExito = document.createElement('div');
    mensajeExito.className = 'mensaje-exito';
    mensajeExito.textContent = mensaje;
    mensajeExito.setAttribute('data-success-for', campo.id);
    
    campo.parentNode.insertBefore(mensajeExito, campo.nextSibling);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        campo.classList.remove('campo-exito');
        if (mensajeExito.parentNode) {
            mensajeExito.remove();
        }
    }, 3000);
}

// ===== CONFIGURACIÓN DE VALIDACIONES EN TIEMPO REAL =====
function configurarValidaciones() {
    // Validación de fechas en tiempo real
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    
    if (fechaInicio && fechaFin) {
        fechaInicio.addEventListener('change', validarFecha);
        fechaFin.addEventListener('change', validarFecha);
    }
    
    // Validación de campos requeridos
    const camposRequeridos = document.querySelectorAll('input[required], textarea[required], select[required]');
    camposRequeridos.forEach(campo => {
        campo.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                mostrarError(this, 'Este campo es obligatorio');
            } else {
                removerError(this);
            }
        });
        
        campo.addEventListener('input', function() {
            if (this.value.trim() !== '') {
                removerError(this);
            }
        });
    });
}

// ===== MANEJO DE CARGA DE ARCHIVOS =====
function configurarCargaArchivos() {
    const imagenInput = document.getElementById('imagen_evento');
    const documentoInput = document.getElementById('documento_evento');
    
    if (imagenInput) {
        imagenInput.addEventListener('change', function() {
            manejarCargaImagen(this);
        });
        
        // Configurar drag and drop
        const imagenArea = document.getElementById('imagen-upload-area');
        if (imagenArea) {
            configurarDragAndDrop(imagenArea, imagenInput);
        }
    }
    
    if (documentoInput) {
        documentoInput.addEventListener('change', function() {
            manejarCargaDocumento(this);
        });
        
        // Configurar drag and drop
        const documentoArea = document.getElementById('documento-upload-area');
        if (documentoArea) {
            configurarDragAndDrop(documentoArea, documentoInput);
        }
    }
}

function manejarCargaImagen(input) {
    const archivo = input.files[0];
    const preview = document.getElementById('previewImagen');
    const placeholder = input.parentNode.querySelector('.upload-placeholder');
    
    if (archivo) {
        // Validar tipo de archivo
        if (!archivo.type.startsWith('image/')) {
            mostrarError(input, 'Por favor selecciona un archivo de imagen válido');
            return;
        }
        
        // Validar tamaño (máximo 5MB)
        if (archivo.size > 5 * 1024 * 1024) {
            mostrarError(input, 'La imagen no puede superar los 5MB');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
        };
        reader.readAsDataURL(archivo);
        
        removerError(input);
        mostrarExito(input, 'Imagen cargada correctamente');
    }
}

function manejarCargaDocumento(input) {
    const archivo = input.files[0];
    const preview = document.getElementById('previewDocumento');
    const placeholder = input.parentNode.querySelector('.upload-placeholder');
    
    if (archivo) {
        // Validar tipo de archivo
        if (archivo.type !== 'application/pdf') {
            mostrarError(input, 'Por favor selecciona un archivo PDF válido');
            return;
        }
        
        // Validar tamaño (máximo 10MB)
        if (archivo.size > 10 * 1024 * 1024) {
            mostrarError(input, 'El PDF no puede superar los 10MB');
            return;
        }
        
        const url = URL.createObjectURL(archivo);
        preview.src = url;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
        
        removerError(input);
        mostrarExito(input, 'Documento cargado correctamente');
    }
}

function configurarDragAndDrop(area, input) {
    area.addEventListener('dragover', function(e) {
        e.preventDefault();
        area.classList.add('drag-over');
    });
    
    area.addEventListener('dragleave', function(e) {
        e.preventDefault();
        area.classList.remove('drag-over');
    });
    
    area.addEventListener('drop', function(e) {
        e.preventDefault();
        area.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// ===== VALIDACIÓN FINAL DEL FORMULARIO =====
function validarFormularioCompleto() {
    const formulario = document.querySelector('form');
    let esValido = true;
    
    // Validar todos los campos requeridos
    const camposRequeridos = formulario.querySelectorAll('input[required], textarea[required], select[required]');
    
    camposRequeridos.forEach(campo => {
        if (campo.value.trim() === '') {
            mostrarError(campo, 'Este campo es obligatorio');
            esValido = false;
        }
    });
    
    // Validar fechas
    if (!validarFecha()) {
        esValido = false;
    }
    
    return esValido;
}

// Event listener para el envío del formulario
document.addEventListener('DOMContentLoaded', function() {
    const formulario = document.querySelector('form');
    if (formulario) {
        formulario.addEventListener('submit', function(e) {
            if (!validarFormularioCompleto()) {
                e.preventDefault();
                alert('Por favor corrige los errores antes de enviar el formulario');
                return false;
            }
            
            // Mostrar loading en el botón de envío
            const botonEnviar = formulario.querySelector('button[type="submit"]');
            if (botonEnviar) {
                botonEnviar.classList.add('loading');
                botonEnviar.disabled = true;
            }
        });
    }
});

  // Mostrar/ocultar campo de modalidad
  tipoEvento.addEventListener("change", function () {
    if (this.value === "competencia") {
      campoParticipacion.style.display = "block";
      tipoParticipacion.setAttribute("required", "true");
    } else {
      campoParticipacion.style.display = "none";
      tipoParticipacion.removeAttribute("required");
      campoMaximo.style.display = "none";
      maxIntegrantes.removeAttribute("required");
    }
  });

  // Mostrar/ocultar campo de máximo integrantes
  tipoParticipacion.addEventListener("change", function () {
    if (this.value === "grupal") {
      campoMaximo.style.display = "block";
      maxIntegrantes.setAttribute("required", "true");
    } else {
      campoMaximo.style.display = "none";
      maxIntegrantes.removeAttribute("required");
    }
  });