document.addEventListener('DOMContentLoaded', function() {
            // Botones de admitir
            document.querySelectorAll('.btn-admitir').forEach(button => {
                button.addEventListener('click', function() {
                    const evaluadorId = this.dataset.id;
                    const eventoId = this.dataset.evento;
                    const nombre = this.dataset.nombre;
                    
                    document.getElementById('mensaje-admitir').textContent = 
                        `¿Está seguro que desea admitir al evaluador ${nombre}?`;
                    document.getElementById('evaluadorIdAdmitir').value = evaluadorId;
                    document.getElementById('eventoIdAdmitir').value = eventoId;
                });
            });

            // Botones de rechazar
            document.querySelectorAll('.btn-rechazar').forEach(button => {
                button.addEventListener('click', function() {
                    const evaluadorId = this.dataset.id;
                    const eventoId = this.dataset.evento;
                    const nombre = this.dataset.nombre;
                    
                    document.getElementById('mensaje-rechazo').textContent = 
                        `¿Está seguro que desea rechazar al evaluador ${nombre}?`;
                    document.getElementById('evaluadorIdRechazo').value = evaluadorId;
                    document.getElementById('eventoIdRechazo').value = eventoId;
                });
            });

            // Confirmar admisión
            document.getElementById('confirmarAdmitir').addEventListener('click', function() {
                const evaluadorId = document.getElementById('evaluadorIdAdmitir').value;
                const eventoId = document.getElementById('eventoIdAdmitir').value;
                
                // Crear formulario para enviar datos
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/administrador/actualizar_evaluador/${evaluadorId}/Admitido/`;
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.innerHTML = `
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <input type="hidden" name="evento_id" value="${eventoId}">
                `;
                
                document.body.appendChild(form);
                form.submit();
            });

            // Confirmar rechazo
            document.getElementById('confirmarRechazo').addEventListener('click', function() {
                const evaluadorId = document.getElementById('evaluadorIdRechazo').value;
                const eventoId = document.getElementById('eventoIdRechazo').value;
                
                // Crear formulario para enviar datos
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/administrador/actualizar_evaluador/${evaluadorId}/Rechazado/`;
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.innerHTML = `
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <input type="hidden" name="evento_id" value="${eventoId}">
                `;
                
                document.body.appendChild(form);
                form.submit();
            });
        });