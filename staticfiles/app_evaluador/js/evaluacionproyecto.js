document.addEventListener('DOMContentLoaded', function () {
    const totalCriterios = document.querySelectorAll('.puntaje-input').length;
    const progressBar = document.getElementById('progressBar');
    const progressPct = document.getElementById('progressPct');
    const errorBox = document.getElementById('error-message');

    // Sincronizar slider <-> número y actualizar display
    function syncScore(idx, val) {
        const v = Math.min(100, Math.max(0, parseInt(val) || 0));
        const disp = document.getElementById('disp-' + idx);
        const num = document.getElementById('num-' + idx);
        const slider = document.querySelector('.eval-slider[data-idx="' + idx + '"]');
        if (disp) disp.textContent = v;
        if (num) num.value = v;
        if (slider) slider.value = v;
        actualizarProgreso();
    }

    // Eventos en sliders
    document.querySelectorAll('.eval-slider').forEach(function (slider) {
        slider.addEventListener('input', function () {
            syncScore(this.dataset.idx, this.value);
        });
    });

    // Eventos en inputs numéricos
    document.querySelectorAll('.puntaje-input').forEach(function (input) {
        input.addEventListener('input', function () {
            syncScore(this.dataset.idx, this.value);
        });
    });

    // Focus en card
    document.querySelectorAll('.puntaje-input, .eval-textarea').forEach(function (el) {
        el.addEventListener('focus', function () {
            const idx = this.dataset.idx !== undefined
                ? this.dataset.idx
                : this.dataset.card;
            const card = document.getElementById('card-' + idx);
            if (card) card.classList.add('focused');
        });
        el.addEventListener('blur', function () {
            const idx = this.dataset.idx !== undefined
                ? this.dataset.idx
                : this.dataset.card;
            const card = document.getElementById('card-' + idx);
            if (card) card.classList.remove('focused');
        });
    });

    // Barra de progreso — cuenta cuántos tienen puntaje > 0
    function actualizarProgreso() {
        let completados = 0;
        document.querySelectorAll('.puntaje-input').forEach(function (input) {
            const v = parseInt(input.value);
            if (!isNaN(v) && v >= 0 && v <= 100 && input.value !== '') completados++;
        });
        const pct = totalCriterios > 0 ? (completados / totalCriterios) * 100 : 0;
        progressBar.style.width = pct + '%';
        progressPct.textContent = completados + ' / ' + totalCriterios;
    }

    // Validación al enviar
    document.getElementById('form-evaluacion').addEventListener('submit', function (e) {
        let valido = true;
        document.querySelectorAll('.puntaje-input').forEach(function (input) {
            const v = parseFloat(input.value);
            if (isNaN(v) || v < 0 || v > 100) valido = false;
        });

        if (!valido) {
            e.preventDefault();
            errorBox.classList.add('visible');
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            errorBox.classList.remove('visible');
        }
    });

    actualizarProgreso();
});