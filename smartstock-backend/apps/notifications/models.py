from django.conf import settings
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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'escalation notification'
        verbose_name_plural = 'escalation notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reason', 'status']),
            models.Index(fields=['po', 'reason']),
        ]

    def __str__(self) -> str:
        return f'Escalation for PO-{self.po_id}: {self.reason} ({self.status})'


class Notification(models.Model):
    class Type(models.TextChoices):
        MONITORING = 'monitoring', 'Monitoring Alert'
        ESCALATION = 'escalation', 'Escalation Notification'
        FORECAST = 'forecast', 'Forecast Alert'
        REORDER = 'reorder', 'Reorder Alert'

    class Severity(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    type = models.CharField(max_length=20, choices=Type.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'
        indexes = [
            models.Index(fields=['type', 'severity', 'created_at'], name='idx_notif_type_sev'),
        ]

    def __str__(self):
        return f'[{self.severity}] {self.title}'


class UserNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_notifications',
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='user_notifications',
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'user notification'
        verbose_name_plural = 'user notifications'
        constraints = [
            models.UniqueConstraint(fields=['user', 'notification'], name='uniq_user_notification')
        ]
        indexes = [
            models.Index(fields=['user', 'is_read'], name='idx_user_notif_read'),
        ]

    def __str__(self):
        return f'{self.user} - {self.notification}'
