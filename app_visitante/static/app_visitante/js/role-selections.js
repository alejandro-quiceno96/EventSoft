// Agregar efecto de ripple en los botones
document.querySelectorAll('.role-button').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        this.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Animación de entrada staggered para los botones
document.querySelectorAll('.role-button').forEach((button, index) => {
    button.style.animationDelay = `${0.1 * index}s`;
    button.style.animation = 'slideInUp 0.6s ease-out both';
});

// Opcional: Agregar efecto de paralaje sutil al mover el mouse
document.addEventListener('mousemove', (e) => {
    const container = document.querySelector('.main-container');
    const rect = container.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = (e.clientX - centerX) / 50;
    const deltaY = (e.clientY - centerY) / 50;
    
    container.style.transform = `perspective(1000px) rotateY(${deltaX}deg) rotateX(${-deltaY}deg)`;
});

// Resetear transformación al salir del área
document.addEventListener('mouseleave', () => {
    const container = document.querySelector('.main-container');
    container.style.transform = 'perspective(1000px) rotateY(0deg) rotateX(0deg)';
});