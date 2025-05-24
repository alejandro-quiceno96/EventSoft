from django.shortcuts import render


# Vista para buscar participante
def buscar_participante(request):
    return render(request, 'participantes/buscar_participante.html')

# Vista para cancelar preinscripción
def cancelar_pre_par(request):
    return render(request, 'participantes/cancelar_pre_par.html')

# Vista para ver eventos del participante
def eventos_participante(request):
    return render(request, 'participaantes/eventos_participante.html')

# Vista para modificar los datos de un participante
def modificar_participante(request):
    return render(request, 'participantes/modificar_participante.html')

# Vista para hacer la preinscripción
def pre_inscripcion(request):
    return render(request, 'participantes/Pre_inscripcion_participante.html')

# Vista para ver la información del participante
def ver_info_participante(request):
    return render(request, 'participantes/ver_info_participante.html')

