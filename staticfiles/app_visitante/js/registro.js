document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const submitBtn = document.querySelector('.submit-btn');
    const strengthBar = document.querySelector('.password-strength');
    const rulesList = document.querySelectorAll('#password-rules li');

    // Asignar placeholders vacíos solo si no existen (para evitar errores)
    document.querySelectorAll('input, select').forEach(input => {
        if (!input.hasAttribute('placeholder')) {
            input.setAttribute('placeholder', '');
        }
    });

    // Auto foco
    document.querySelector('input')?.focus();

    // Toggle mostrar/ocultar contraseña
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function () {
            const input = this.previousElementSibling;
            this.classList.toggle('show');
            input.type = input.type === 'password' ? 'text' : 'password';
        });
    });

    // Validación de contraseña
    const validarPassword = () => {
        const p1 = password1.value;
        const p2 = password2.value;

        const length = p1.length >= 8;
        const uppercase = /[A-Z]/.test(p1);
        const number = /[0-9]/.test(p1);
        const special = /[^A-Za-z0-9]/.test(p1);
        const tieneLetra = /[a-zA-Z]/.test(p1);
        const match = p1 === p2 && p2.length > 0;

        // Actualizar reglas visuales
        document.querySelector('[data-rule="length"]').classList.toggle('valid', length);
        document.querySelector('[data-rule="length"]').classList.toggle('invalid', !length && p1.length > 0);

        document.querySelector('[data-rule="uppercase"]').classList.toggle('valid', uppercase);
        document.querySelector('[data-rule="uppercase"]').classList.toggle('invalid', !uppercase && p1.length > 0);

        document.querySelector('[data-rule="number"]').classList.toggle('valid', number);
        document.querySelector('[data-rule="number"]').classList.toggle('invalid', !number && p1.length > 0);

        document.querySelector('[data-rule="special"]').classList.toggle('valid', special);
        document.querySelector('[data-rule="special"]').classList.toggle('invalid', !special && p1.length > 0);

        document.querySelector('[data-rule="match"]').classList.toggle('valid', match);
        document.querySelector('[data-rule="match"]').classList.toggle('invalid', !match && p2.length > 0);

        // Fuerza visual
        let fuerza = 0;
        if (length) fuerza += 25;
        if (uppercase) fuerza += 25;
        if (number) fuerza += 25;
        if (special) fuerza += 25;

        strengthBar.style.width = `${fuerza}%`;
        if (fuerza === 0) strengthBar.style.background = 'var(--borde)';
        else if (fuerza < 50) strengthBar.style.background = '#ef4444';
        else if (fuerza < 75) strengthBar.style.background = '#f59e0b';
        else strengthBar.style.background = '#10b981';

        // Habilitar botón: mínimo 8 chars, al menos una letra (no solo numérica), coinciden
        const reglasMinimas = length && tieneLetra && match;
        submitBtn.disabled = !reglasMinimas;
    };

    password1.addEventListener('input', validarPassword);
    password2.addEventListener('input', validarPassword);

    // Evitar doble envío
    form.addEventListener('submit', function (e) {
        if (submitBtn.disabled) {
            e.preventDefault();
            submitBtn.classList.add('error');
            return false;
        }

        submitBtn.disabled = true;
        submitBtn.querySelector('span').textContent = 'Creando cuenta...';
    });

    // Scroll a errores
    const primerError = document.querySelector('.errorlist, .alert-error');
    if (primerError) {
        primerError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => primerError.classList.add('error'), 100);
    }
});