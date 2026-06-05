from django.db import models


class AuditLog(models.Model):
    event = models.CharField(max_length=50)
    user = models.ForeignKey(
        'authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True
    )
    entity_id = models.IntegerField(null=True, blank=True)
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.event} by {self.user} at {self.timestamp}"
