function habilitarInput(idInput) {
    const input = document.getElementById(idInput);
    input.disabled = !input.disabled;
    if (!input.disabled) input.focus();
}

function habilitarTodosLosInputs() {
    const inputs = document.querySelectorAll('#modalEditarEvaluador input');
    inputs.forEach(input => {
      input.disabled = false;
    });
  }