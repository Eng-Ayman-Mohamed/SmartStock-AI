
from django.db import models


class AuditLog(models.Model):
    # What happened
    event = models.CharField(max_length=100)         # e.g. "USER_LOGIN", "PO_APPROVED", "AI_NL_QUERY"
    entity_type = models.CharField(max_length=100, blank=True)  # e.g. "PurchaseOrder", "User"
    entity_id = models.IntegerField(null=True, blank=True)

    # Who did it
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
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
        return f"{self.event} by {self.user} at {self.timestamp}"