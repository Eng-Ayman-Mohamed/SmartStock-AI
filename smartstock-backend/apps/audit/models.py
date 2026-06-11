from django.db import models


class AuditEvent(models.TextChoices):
    USER_LOGIN = 'USER_LOGIN'
    PO_CREATED = 'PO_CREATED'
    PO_APPROVED = 'PO_APPROVED'
    PO_REJECTED = 'PO_REJECTED'
    PO_SENT = 'PO_SENT'
    STOCK_ADJUSTED = 'STOCK_ADJUSTED'
    PRODUCT_CREATED = 'PRODUCT_CREATED'
    PRODUCT_UPDATED = 'PRODUCT_UPDATED'
    INVOICE_CONFIRMED = 'INVOICE_CONFIRMED'
    INVOICE_REJECTED = 'INVOICE_REJECTED'
    PROMPT_INJECTION_ATTEMPT = 'PROMPT_INJECTION_ATTEMPT'
    AI_RAG_QUERY = 'AI_RAG_QUERY'
    VISION_EXTRACTION_FAILED = 'VISION_EXTRACTION_FAILED'
    AGENT_RUN_COMPLETED = 'AGENT_RUN_COMPLETED'


class AuditLog(models.Model):
    # What happened
    event = models.CharField(
        max_length=100, choices=AuditEvent.choices
    )  # e.g. "USER_LOGIN", "PO_APPROVED", "AI_NL_QUERY"
    entity_type = models.CharField(max_length=100, blank=True)  # e.g. "PurchaseOrder", "User"
    entity_id = models.IntegerField(null=True, blank=True)

    # Who did it
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # What the data looked like at the time
    data_snapshot = models.JSONField(default=dict)

    # When
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.event} by {self.user} at {self.timestamp}'


class AgentRun(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    agent_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.agent_name}: {self.status}'
