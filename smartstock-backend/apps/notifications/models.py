from django.db import models


class EscalationNotification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        IN_APP = 'in_app', 'In-App'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    class Reason(models.TextChoices):
        EMAIL_DELIVERY_FAILED = 'email_delivery_failed', 'Email Delivery Failed'
        SUPPLIER_TIMEOUT = 'supplier_timeout', 'Supplier Timeout'
        OTHER = 'other', 'Other'

    po = models.ForeignKey(
        'purchasing.PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='escalation_notifications',
    )
    reason = models.CharField(max_length=50, choices=Reason.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.EMAIL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    recipient_email = models.EmailField(blank=True)
    message = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reason', 'status']),
            models.Index(fields=['po', 'reason']),
        ]

    def __str__(self) -> str:
        return f'Escalation for PO-{self.po_id}: {self.reason} ({self.status})'
