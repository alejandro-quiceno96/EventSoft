import os
import django
from django.core.mail import send_mail
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pr_eventsoft.settings')
django.setup()

def test_send_email():
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        send_mail(
            'Test Email from EventSoft',
            'This is a test message to verify Brevo configuration.',
            settings.DEFAULT_FROM_EMAIL,
            ['eventsoft3@gmail.com'],
            fail_silently=False,
        )
        print("SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"ERROR: Failed to send email. {e}")

if __name__ == "__main__":
    test_send_email()
