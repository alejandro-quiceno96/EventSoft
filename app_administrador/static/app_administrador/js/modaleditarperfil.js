// Toggle de campos de contraseña
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordCheckbox = document.getElementById('changePassword');
    const passwordFields = document.getElementById('passwordFields');
    
    if (changePasswordCheckbox && passwordFields) {
        changePasswordCheckbox.addEventListener('change', function() {
            if (this.checked) {
                passwordFields.style.display = 'block';
                passwordFields.classList.add('fade-in');
                // Hacer campos requeridos
                document.getElementById('currentPassword').required = true;
                document.getElementById('newPassword').required = true;
                document.getElementById('confirmPassword').required = true;
            } else {
                passwordFields.style.display = 'none';
                passwordFields.classList.remove('fade-in');
                // Limpiar campos y quitar required
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmPassword').value = '';
                document.getElementById('currentPassword').required = false;
                document.getElementById('newPassword').required = false;
                document.getElementById('confirmPassword').required = false;
            }
        });
    }
});

// Función para validar contraseñas
function validatePasswords() {
    const changePasswordCheck = document.getElementById('changePassword');
    
    if (!changePasswordCheck.checked) {
        return true; // No necesita validación si no se va a cambiar
    }
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validar que todos los campos estén llenos
    if (!currentPassword || !newPassword || !confirmPassword) {
        showToast('Por favor completa todos los campos de contraseña', 'error');
        return false;
    }
    
    // Validar que las contraseñas coincidan
    if (newPassword !== confirmPassword) {
        showToast('Las contraseñas no coinciden', 'error');
        document.getElementById('confirmPassword').focus();
        return false;
    }
    
    // Validar longitud mínima
    if (newPassword.length < 8) {
        showToast('La nueva contraseña debe tener al menos 8 caracteres', 'error');
        document.getElementById('newPassword').focus();
        return false;
    }
    
    // Validar complejidad de contraseña
    if (!isPasswordStrong(newPassword)) {
        showToast('La contraseña debe contener al menos una mayúscula, una minúscula y un número', 'error');
        document.getElementById('newPassword').focus();
        return false;
    }
    
    return true;
}

// Función para validar fortaleza de contraseña
function isPasswordStrong(password) {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    return hasUpperCase && hasLowerCase && hasNumbers;
}

// Función para guardar el perfil
function saveProfile() {
    const form = document.getElementById('editProfileForm');
    const saveBtn = document.querySelector('[onclick="saveProfile()"]');
    
    // Validar formulario
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Validar contraseñas si están habilitadas
    if (!validatePasswords()) {
        return;
    }
    
    // Mostrar estado de carga
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
    saveBtn.disabled = true;
    saveBtn.classList.add('btn-loading');
    
    // Preparar datos del formulario
    const formData = new FormData(form);
    
    // Si no se va a cambiar la contraseña, remover esos campos
    const changePasswordCheck = document.getElementById('changePassword');
    if (!changePasswordCheck.checked) {
        formData.delete('current_password');
        formData.delete('new_password');
        formData.delete('confirm_password');
    }
    
    // Enviar datos al servidor
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Éxito
            saveBtn.innerHTML = '<i class="fas fa-check me-1"></i>Guardado';
            saveBtn.classList.remove('btn-loading');
            
            setTimeout(() => {
                saveBtn.innerHTML = originalText;
                saveBtn.disabled = false;
                
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                modal.hide();
                
                // Mostrar mensaje de éxito
                showToast('Perfil actualizado correctamente', 'success');
                
                // Actualizar información en la página si es necesario
                updateProfileDisplay(data.user);
                
            }, 1000);
        } else {
            // Error
            throw new Error(data.message || 'Error al actualizar el perfil');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        saveBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
        saveBtn.classList.remove('btn-loading');
        
        setTimeout(() => {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }, 2000);
        
        showToast(error.message || 'Error al actualizar el perfil', 'error');
    });
}

// Función para mostrar notificaciones toast
function showToast(message, type = 'success') {
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'toast-success' : 'toast-error';
    const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999;" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${iconClass} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remover toast del DOM después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Función para actualizar la información mostrada en el perfil
function updateProfileDisplay(userData) {
    // Actualizar elementos del sidebar si existen
    const profileElements = {
        '.profile-item-value': userData.full_name,
        '[data-profile="email"] .profile-item-value': userData.email,
        '[data-profile="username"] .profile-item-value': userData.username,
        '[data-profile="phone"] .profile-item-value': userData.telefono,
        '[data-profile="birthdate"] .profile-item-value': userData.fecha_nacimiento
    };
    
    Object.entries(profileElements).forEach(([selector, value]) => {
        const element = document.querySelector(selector);
        if (element && value) {
            element.textContent = value;
        }
    });
}

// Validación en tiempo real para campos de contraseña
document.addEventListener('DOMContentLoaded', function() {
    const newPasswordField = document.getElementById('newPassword');
    const confirmPasswordField = document.getElementById('confirmPassword');
    
    if (newPasswordField) {
        newPasswordField.addEventListener('input', function() {
            validatePasswordStrength(this);
        });
    }
    
    if (confirmPasswordField) {
        confirmPasswordField.addEventListener('input', function() {
            validatePasswordMatch();
        });
    }
});

// Función para validar fortaleza de contraseña en tiempo real
function validatePasswordStrength(input) {
    const password = input.value;
    const isStrong = password.length >= 8 && isPasswordStrong(password);
    
    if (password.length > 0) {
        if (isStrong) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    } else {
        input.classList.remove('is-valid', 'is-invalid');
    }
}

// Función para validar coincidencia de contraseñas
function validatePasswordMatch() {
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const confirmField = document.getElementById('confirmPassword');
    
    if (confirmPassword.length > 0) {
        if (newPassword === confirmPassword) {
            confirmField.classList.remove('is-invalid');
            confirmField.classList.add('is-valid');
        } else {
            confirmField.classList.remove('is-valid');
            confirmField.classList.add('is-invalid');
        }
    } else {
        confirmField.classList.remove('is-valid', 'is-invalid');
    }
}

// Limpiar formulario cuando se cierra el modal
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            // Resetear checkbox de contraseña
            const changePasswordCheck = document.getElementById('changePassword');
            const passwordFields = document.getElementById('passwordFields');
            
            if (changePasswordCheck) {
                changePasswordCheck.checked = false;
                passwordFields.style.display = 'none';
                
                // Limpiar campos de contraseña
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmPassword').value = '';
                
                // Remover clases de validación
                document.querySelectorAll('.is-valid, .is-invalid').forEach(el => {
                    el.classList.remove('is-valid', 'is-invalid');
                });
            }
        });
    }
});