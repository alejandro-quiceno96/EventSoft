from django.shortcuts import render

def inicio(request):
    # Obtener eventos (si tienes el modelo)
    # eventos = Evento.objects.all()
    
    # Por ahora con datos hardcodeados como en tu ejemplo
    context = {
        'administrador': 'Juan Garcia',
        # 'eventos': eventos,  # Descomenta cuando tengas el modelo
    }
    
    return render(request, 'app_administrador/admin.html', context)