from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Application

@receiver(post_save, sender=Application)
def notify_application_status(sender, instance, created, **kwargs):
    # Haddii codsigu hadda dhashay (Submitted)
    if created:
        subject = f"Codsigaga {instance.scholarship.title}"
        message = f"Salaan {instance.user.username},\nCodsigaaga waa la helay. Xaaladdiisu waa: {instance.status}."
    
    # Haddii Admin-ku hadda beddelay status-ka (tusaale: Approved)
    else:
        subject = f"Cusboonaysiin: {instance.scholarship.title}"
        message = f"Salaan {instance.user.username},\nXaaladda codsigaaga deeqda waa la beddelay. Hadda waa: {instance.status}."

    # Diritaanka Email-ka
    send_mail(
        subject,
        message,
        'scholarai@gmail.com',
        [instance.user.email],
        fail_silently=False,
    )