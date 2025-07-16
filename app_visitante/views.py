from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from app_eventos.models import Eventos, AsistentesEventos
from app_categorias.models import Categorias
from app_areas.models import Areas  # O Area si renombraste la clase
from app_eventos.models import Eventos,  ParticipantesEventos, EvaluadoresEventos
from django.views.decorators.csrf import csrf_exempt
from app_participante.models import Participantes
from app_asistente.models import Asistentes
from app_evaluador.models import Evaluadores
from app_super_admin.models import SuperAdministradores
from app_administrador.models import Administradores
from django.utils import timezone
from django.urls import reverse
from app_administrador.utils import generar_pdf, generar_clave_acceso
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .forms import RegistroUsuarioForm
from app_usuarios.models import Usuario
from django.db import IntegrityError
from django.contrib import messages
from django.views.decorators.http import require_http_methods

def login_view(request):
    if request.method == 'POST':
        identificador = request.POST['username']
        password = request.POST['password']

        try:
            if '@' in identificador:
                user = Usuario.objects.get(email=identificador)
            else:
                user = Usuario.objects.get(username=identificador)
        except Usuario.DoesNotExist:
            return render(request, 'app_visitante/login.html')

        usuario = authenticate(request, username=user.username, password=password)

        if usuario is not None:
            # Verificar roles desde tus modelos
            roles = []
            if SuperAdministradores.objects.filter(usuario=usuario).exists():
                roles.append('Super Administrador')
            if Administradores.objects.filter(usuario=usuario).exists():
                roles.append('Administrador de Eventos')

            # Guardamos ID en sesión para confirmación de rol
            request.session['prelogin_user_id'] = usuario.id

            if len(roles) >= 1:
                return render(request, 'app_visitante/seleccionar_rol.html', {'roles': roles, 'usuario': usuario})
            else:
                auth_login(request, usuario)
                return redirect('inicio_visitante')  # o ruta por defecto
        else:
            messages.error(request, 'Contraseña incorrecta.')
    return render(request, 'app_visitante/login.html')


def registro_usuario_view(request):
    """
    Vista para registrar un nuevo usuario
    """
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                messages.success(request, 'Cuenta creada exitosamente.')
                return redirect('login')
            except IntegrityError:
                messages.error(request, 'Ya existe un usuario con este documento.')
            except Exception as e:
                messages.error(request, f'Ocurrió un error: {str(e)}')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'app_visitante/registro.html', {'form': form})

@require_http_methods(["POST"])
def verificar_documento(request):
    try:
        data = json.loads(request.body)
        documento = data.get('documento_identidad')
        if documento:
            existe = Usuario.objects.filter(documento_identidad=documento).exists()
            return JsonResponse({'existe': existe})
        return JsonResponse({'error': 'Documento no proporcionado.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Error del servidor.'}, status=500)


def inicio_visitante(request):
    eventos = Eventos.objects.all()

    categoria = request.GET.get('categoria')
    area = request.GET.get('area')
    fecha_inicio = request.GET.get('fecha_inicio')


    # Filtrar por categoría (a través del modelo intermedio)
    if categoria:
        eventos = eventos.filter(eventoscategorias__eve_cat_categoria_fk=categoria)

    # Filtrar por área (a través de categoria relacionada al evento)
    if area:
        eventos = eventos.filter(
            eventoscategorias__eve_cat_categoria_fk__cat_area_fk=area
        )

    # Filtrar por fecha de inicio
    if fecha_inicio:
        eventos = eventos.filter(eve_fecha_inicio=fecha_inicio)

    eventos = eventos.distinct()  # Evitar duplicados por joins

    categorias = Categorias.objects.all()
    areas = Areas.objects.all()
    if request.user.is_authenticated:
        roles = []
        if SuperAdministradores.objects.filter(usuario=request.user).exists():
            roles.append('Super Administrador')
        if Administradores.objects.filter(usuario=request.user).exists():
            roles.append('Administrador de Eventos')
    
    contexto = {
        'eventos': eventos,
        'categorias': categorias,
        'areas': areas,
        'roles': roles if request.user.is_authenticated else [],
    }

    return render(request, 'app_visitante/index.html', contexto)



def inicio_sesion_administrador(request):
    return render(request, 'app_visitante/inicio_sesion_administrador.html')

def inicio_evaluador(request):
    return render(request, 'app_visitante/inicio_sesion_evaluador.html')


def detalle_evento(request, evento_id):
    """
    Vista para mostrar el detalle de un evento con información adicional
    """
    evento = get_object_or_404(Eventos, pk=evento_id)
    
    # Obtener información adicional del evento
    participantes = ParticipantesEventos.objects.filter(
        par_eve_evento_fk=evento_id
    ).select_related('par_eve_participante_fk')
    
    evaluadores = EvaluadoresEventos.objects.filter(
        eva_eve_evento_fk=evento_id
    ).select_related('eva_eve_evaluador_fk')
    
    asistentes = AsistentesEventos.objects.filter(
        asi_eve_evento_fk=evento_id
    ).select_related('asi_eve_asistente_fk')

    # Calcular totales
    total_participantes = participantes.count()
    total_evaluadores = evaluadores.count()
    total_asistentes = asistentes.count()
    total_inscritos = total_participantes + total_evaluadores + total_asistentes

    # Determinar roles del usuario actual
    roles = []
    usuario_inscrito = False
    usuario_inscrito_participante = False
    usuario_inscrito_evaluador = False
    usuario_inscrito_asistente = False

    estado_participante = None
    estado_evaluador = None
    estado_asistente = None

    if request.user.is_authenticated:
        usuario = request.user

        # Verificar roles
        if Participantes.objects.filter(usuario=usuario).exists():
            roles.append('Participante')
        if Asistentes.objects.filter(usuario=usuario).exists():
            roles.append('Asistente')
        if Evaluadores.objects.filter(usuario=usuario).exists():
            roles.append('Evaluador')

        # Estado del participante
        participante_evento = ParticipantesEventos.objects.filter(
            par_eve_evento_fk=evento_id,
            par_eve_participante_fk__usuario=usuario
        ).first()
        if participante_evento:
            estado_participante = participante_evento.estado
            usuario_inscrito_participante = estado_participante == 'activo'

        # Estado del evaluador
        evaluador_evento = EvaluadoresEventos.objects.filter(
            eva_eve_evento_fk=evento_id,
            eva_eve_evaluador_fk__usuario=usuario
        ).first()
        if evaluador_evento:
            estado_evaluador = evaluador_evento.estado
            usuario_inscrito_evaluador = estado_evaluador == 'activo'

        # Estado del asistente
        asistente_evento = AsistentesEventos.objects.filter(
            asi_eve_evento_fk=evento_id,
            asi_eve_asistente_fk__usuario=usuario
        ).first()
        if asistente_evento:
            estado_asistente = asistente_evento.estado
            usuario_inscrito_asistente = estado_asistente == 'activo'

        # Inscripción activa en cualquiera de los roles
        usuario_inscrito = (
            usuario_inscrito_participante or 
            usuario_inscrito_evaluador or 
            usuario_inscrito_asistente
        )

    context = {
        'evento': evento,
        'participantes': participantes,
        'evaluadores': evaluadores,
        'asistentes': asistentes,
        'total_participantes': total_participantes,
        'total_evaluadores': total_evaluadores,
        'total_asistentes': total_asistentes,
        'total_inscritos': total_inscritos,
        'roles': roles,
        'usuario_inscrito': usuario_inscrito,
        'usuario_inscrito_participante': usuario_inscrito_participante,
        'usuario_inscrito_evaluador': usuario_inscrito_evaluador,
        'usuario_inscrito_asistente': usuario_inscrito_asistente,
        'estado_participante': estado_participante,
        'estado_evaluador': estado_evaluador,
        'estado_asistente': estado_asistente,
    }
    
    return render(request, 'app_visitante/detalle_evento.html', context)


@login_required(login_url='login')
def preinscripcion_participante(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    return render(request, 'app_visitante/Pre_inscripcion_participante.html', {'evento': evento})

@login_required(login_url='login')
def preinscripcion_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)

    if not evento.eve_tienecosto:
        # Redirige a una plantilla que envía un POST automáticamente
        return render(request, 'app_visitante/post_asistente.html', {
            'evento_id': evento.id
        })
    else:
        return render(request, 'app_visitante/registro_asistente.html', {'evento': evento})

@login_required(login_url='login')
def preinscripcion_evaluador(request, evento_id):
    evento = get_object_or_404(Eventos, id=evento_id)
    return render(request, 'app_visitante/preinscripcion_evaluador.html', {'evento': evento})

def modificar_participante(request):
    return render(request, 'app_visitante/modificar_participante.html')




@login_required(login_url='login')
def submit_preinscripcion_participante(request):
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')
        documento = request.FILES.get('par_eve_documentos')
        # Verificar si el participante ya existe
        try:
            participante = Participantes.objects.get(usuario = request.user)
        except Participantes.DoesNotExist:
            # Si no existe, crear un nuevo participante
            participante = Participantes.objects.create(
                usuario = request.user,
            )

        # Obtener el evento
        try:
            evento = Eventos.objects.get(pk=evento_id)
        except Eventos.DoesNotExist:
            # Si el evento no existe, redirigir a una página de error o inicio
            return redirect('inicio_visitante')

        # Crear la inscripción del participante al evento
        ParticipantesEventos.objects.create(
            par_eve_participante_fk=participante,
            par_eve_evento_fk=evento,
            par_eve_fecha_hora=timezone.now(),
            par_eve_documentos=documento,
            par_eve_estado='Pendiente',  # Puedes cambiar este valor según tu lógica
            par_eve_qr='',  # Debes subir o generar uno real
            par_eve_clave=''  # Idealmente deberías generar una clave segura
        )

        # Redirigir a la página de inicio del visitante
        return redirect(reverse('inicio_visitante') + '?registro=exito_participante')

    # Si no es POST, redirigir a la página de inicio del visitante
    return redirect('inicio_visitante')



@login_required(login_url='login')
def registrar_asistente(request, evento_id):
    evento = get_object_or_404(Eventos, pk=evento_id)

    if request.method == 'POST':
        documento = request.FILES.get('comprobante_pago')

        # Verificar si el usuario ya es un asistente registrado
        try:
            asistente = Asistentes.objects.get(usuario_id=request.user.id)
        except Asistentes.DoesNotExist:
            # Si no existe, crear un nuevo asistente
            asistente = Asistentes.objects.create(
                usuario_id = request.user.id,
            )

        # Crear la inscripción del asistente al evento
        if evento.eve_tienecosto:
            estado = 'Pendiente'
            qr = ''
            clave = ''
        else:
            estado = 'Admitido'
            qr = generar_pdf(asistente.id, 'Asistente', evento_id, tipo="asistente")
            clave = generar_clave_acceso()

        asistente_evento = AsistentesEventos.objects.create(
            asi_eve_asistente_fk=asistente,
            asi_eve_evento_fk=evento,
            asi_eve_fecha_hora=timezone.now(),
            asi_eve_soporte=documento,
            asi_eve_estado=estado,
            asi_eve_qr=qr,
            asi_eve_clave=clave
        )
        asistente_evento.save()

                
    return redirect(reverse('inicio_visitante') + '?registro=exito_asistente')

@login_required(login_url='login')
def registrar_evaluador(request, evento_id):
    """
    Vista para registrar un evaluador en un evento
    Valida que no esté ya inscrito para evitar duplicados
    """
    if request.method == 'POST':
        documento = request.FILES.get('documento')
        
        try:
            # Obtener o crear el evaluador
            evaluador, created = Evaluadores.objects.get_or_create(
                usuario=request.user
            )
        except Exception as e:
            print(f"Error al obtener/crear evaluador: {e}")
            return redirect(reverse('inicio_visitante') + '?error=evaluador')
        
        try:
            # Verificar que el evento existe
            evento = Eventos.objects.get(id=evento_id)
        except Eventos.DoesNotExist:
            return redirect(reverse('inicio_visitante') + '?error=evento_no_existe')
        
        # VALIDACIÓN: Verificar si ya está inscrito como evaluador
        evaluador_ya_inscrito = EvaluadoresEventos.objects.filter(
            eva_eve_evaluador_fk=evaluador,
            eva_eve_evento_fk=evento
        ).exists()
        
        if evaluador_ya_inscrito:
            # Ya está inscrito, redirigir con mensaje de error
            return redirect(reverse('inicio_visitante') + '?error=ya_inscrito_evaluador')
        
        try:
            # Crear la inscripción del evaluador al evento
            EvaluadoresEventos.objects.create(
                eva_eve_evaluador_fk=evaluador,
                eva_eve_evento_fk=evento,
                eva_eve_fecha_hora=timezone.now(),
                eva_eve_documentos=documento,
                eva_estado='Pendiente',
                eva_eve_qr='',
            )
            
            # Redirige con mensaje de éxito
            return redirect(reverse('inicio_visitante') + '?registro=exito_evaluador')
            
        except Exception as e:
            print(f"Error al crear inscripción de evaluador: {e}")
            return redirect(reverse('inicio_visitante') + '?error=inscripcion_fallida')
    
    # Si no es POST, redirigir
    return redirect('inicio_visitante')



respuestas = {
    "hola": "¡Hola! Soy el asistente virtual de EventSoft. ¿En qué puedo ayudarte?",
    "que hace un participante?": "Un participante puede asistir a conferencias, talleres y recibir certificados de participación.",
    "que hace un visitante?": "Un visitante puede recorrer el evento, conocer los stands, pero no participa en las actividades certificadas.",
    "cómo me inscribo?": "Puedes inscribirte desde la página principal, usando el botón de inscripción o accediendo con tu número de documento.",
    "cuáles son los eventos disponibles?": "Puedes ver los eventos disponibles en la sección principal o usar los filtros por categoría y área.",
    "documentos": "Para participar solo necesitas tu documento de identidad y, si aplica, la invitación del evento.",
}

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        mensaje = data.get("mensaje", "").lower()

        for clave, respuesta in respuestas.items():
            if clave in mensaje:
                return JsonResponse({"respuesta": respuesta})

        return JsonResponse({"respuesta": "Lo siento, no entendí tu pregunta. ¿Podrías reformularla?"})

def confirmar_rol(request):
    if request.method == 'POST':
        user_id = request.session.get('prelogin_user_id')
        rol = request.POST.get('rol')

        if not user_id:
            return redirect('login')

        usuario = get_object_or_404(Usuario, id=user_id)
        auth_login(request, usuario)

        if rol == 'Super Administrador':
            return redirect('super_admin:index_super_admin')
        elif rol == 'Administrador de Eventos':
            return redirect('administrador:index_administrador')
        elif rol == 'Visitante':
            return redirect('inicio_visitante')  # Asegúrate de definir esta ruta

def cerrar_sesion(request):
    logout(request)
    return redirect('inicio_visitante')

login_required(login_url='login')  # Protege la vista para usuarios logueados
def editar_perfil(request):
    user = request.user  # Es instancia de tu modelo Usuario

    if request.method == 'POST':
        # Campos básicos
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.username = request.POST.get('username', '')
        user.email = request.POST.get('email', '')

        # Campos adicionales de tu modelo
        user.segundo_nombre = request.POST.get('segundo_nombre', '')
        user.segundo_apellido = request.POST.get('segundo_apellido', '')
        user.telefono = request.POST.get('telefono', '')
        user.fecha_nacimiento = request.POST.get('fecha_nacimiento', '')

        # Manejo de contraseña si el usuario desea cambiarla
        if request.POST.get('current_password'):
            current_password = request.POST.get('current_password')
            if user.check_password(current_password):
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                if new_password == confirm_password and new_password != '':
                    user.set_password(new_password)
                    update_session_auth_hash(request, user)  # Mantener sesión
                    messages.success(request, 'Contraseña actualizada correctamente.')
                else:
                    messages.error(request, 'Las contraseñas no coinciden o están vacías.')
                    return redirect('inicio_visitante')
            else:
                messages.error(request, 'La contraseña actual es incorrecta.')
                return redirect('inicio_visitante')

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('inicio_visitante')  # Redirige a la página de inicio del visitante

    return redirect('inicio_visitante')  # Redirige a la página de inicio si no es POST
