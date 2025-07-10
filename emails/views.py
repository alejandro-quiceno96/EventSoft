from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render

def enviar_correo(request):
    if request.method == 'POST':
        destinatario = request.POST['destinatario']
        asunto = request.POST['asunto']
        mensaje = request.POST['mensaje']
        archivo = request.FILES.get('archivo')

        cuerpo_html = render_to_string('emails/plantilla_email.html', {
            'asunto': asunto,
            'mensaje': mensaje,
        })

        email = EmailMessage(
            subject=asunto,
            body=cuerpo_html,
            from_email='eventsoft3@gmail.com',
            to=['santiagomolano221@gmail.com'],
        )
        email.content_subtype = 'html'

        if archivo:
            email.attach(archivo.name, archivo.read(), archivo.content_type)

        email.send()

        return render(request, 'emails/enviar_correo.html', {'enviado': True})

    return render(request, 'emails/enviar_correo.html')
