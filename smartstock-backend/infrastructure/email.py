from django.core.mail import send_mail
from django.conf import settings


class EmailService:
    def send(self, subject: str, message: str, recipient: str):
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
