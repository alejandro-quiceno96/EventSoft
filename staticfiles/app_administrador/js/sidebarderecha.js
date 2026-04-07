// JavaScript para mejorar la experiencia del sidebar de perfil
document.addEventListener('DOMContentLoaded', function() {
    const perfilSidebar = document.getElementById('perfilSidebar');
    const profileItems = document.querySelectorAll('.profile-item');
    const logoutBtn = document.querySelector('.logout-btn');

    // Animación de entrada para los elementos del perfil
    if (perfilSidebar) {
        perfilSidebar.addEventListener('shown.bs.offcanvas', function() {
            profileItems.forEach((item, index) => {
                setTimeout(() => {
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(20px)';
                    item.style.transition = 'all 0.5s ease';
                    
                    requestAnimationFrame(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    });
                }, index * 100);
            });
        });

        // Resetear animaciones al cerrar
        perfilSidebar.addEventListener('hidden.bs.offcanvas', function() {
            profileItems.forEach(item => {
                item.style.opacity = '';
                item.style.transform = '';
                item.style.transition = '';
            });
        });
    }

    // Efecto de ripple para el botón de logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';
            ripple.style.pointerEvents = 'none';
            ripple.style.animation = 'ripple 0.6s ease-out';
            ripple.style.zIndex = '1';
            
            this.style.position = 'relative';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }

    // Efecto hover mejorado para los items del perfil
    profileItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(8px) scale(1.02)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });

    // Animación del avatar
    const profileAvatar = document.querySelector('.profile-avatar');
    if (profileAvatar) {
        let hoverTimeout;
        
        profileAvatar.addEventListener('mouseenter', function() {
            clearTimeout(hoverTimeout);
            this.style.transform = 'scale(1.1) rotate(5deg)';
            this.style.transition = 'all 0.3s ease';
        });
        
        profileAvatar.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
            hoverTimeout = setTimeout(() => {
                this.style.transition = '';
            }, 300);
        });
    }

    // Efecto de paralaje sutil para elementos decorativos
    const decorativeElements = document.querySelectorAll('.decorative-circle');
    
    if (perfilSidebar && decorativeElements.length > 0) {
        perfilSidebar.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            
            decorativeElements.forEach((element, index) => {
                const speed = (index + 1) * 0.5;
                const xMove = (x - 0.5) * speed * 10;
                const yMove = (y - 0.5) * speed * 10;
                
                element.style.transform = `translate(${xMove}px, ${yMove}px)`;
                element.style.transition = 'transform 0.3s ease';
            });
        });
        
        perfilSidebar.addEventListener('mouseleave', function() {
            decorativeElements.forEach(element => {
                element.style.transform = 'translate(0, 0)';
            });
        });
    }
});

// Función para copiar información al clipboard (funcionalidad extra)
function copyToClipboard(text, element) {
    navigator.clipboard.writeText(text).then(function() {
        // Mostrar feedback visual
        const originalBg = element.style.background;
        element.style.background = 'rgba(0, 120, 50, 0.2)';
        element.style.transition = 'background 0.3s ease';
        
        setTimeout(() => {
            element.style.background = originalBg;
        }, 1000);
        
        // Opcional: mostrar tooltip o notificación
        console.log('Copiado al portapapeles: ' + text);
    }).catch(function(err) {
        console.error('Error al copiar: ', err);
    });
}

// Agregar funcionalidad de copia a los elementos del perfil (opcional)
document.addEventListener('DOMContentLoaded', function() {
    const profileValues = document.querySelectorAll('.profile-item-value');
    
    profileValues.forEach(value => {
        value.addEventListener('dblclick', function() {
            const text = this.textContent.trim();
            if (text && text !== '') {
                copyToClipboard(text, this);
            }
        });
        
        // Agregar cursor pointer para indicar que es clickeable
        value.style.cursor = 'pointer';
        value.title = 'Doble click para copiar';
    });
});