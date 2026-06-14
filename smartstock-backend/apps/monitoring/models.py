from django.db import models


class AlertSeverity(models.TextChoices):
    INFO = 'info', 'Info'
    WARNING = 'warning', 'Warning'
    CRITICAL = 'critical', 'Critical'


class AlertStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    FIRING = 'firing', 'Firing'
    RESOLVED = 'resolved', 'Resolved'


class AlertRule(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=20, choices=AlertSeverity.choices, default=AlertSeverity.WARNING
    )
    metric_name = models.CharField(max_length=200)
    threshold = models.FloatField()
    evaluation_window_minutes = models.IntegerField(default=5)
    enabled = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.severity})'


class AlertEvent(models.Model):
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(
        max_length=20, choices=AlertStatus.choices, default=AlertStatus.PENDING
    )
    triggered_value = models.FloatField(null=True, blank=True)
    message = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    dashboard_notified = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rule', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Alert: {self.rule.name} - {self.status} at {self.created_at}'


class DashboardBanner(models.Model):
    class Level(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'

    title = models.CharField(max_length=200)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    alert_event = models.ForeignKey(
        AlertEvent, on_delete=models.CASCADE, null=True, blank=True, related_name='banners'
    )
    dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dismissed', 'level']),
        ]

    def __str__(self):
        return f'{self.level}: {self.title}'


class TokenUsageLog(models.Model):
    total_tokens = models.IntegerField(default=0)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    daily_total = models.IntegerField(default=0)
    logged_at = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['logged_at']),
        ]

    def __str__(self):
        return f'Tokens: {self.total_tokens} on {self.logged_at}'


class AgentRunLog(models.Model):
    class Outcome(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'

    agent_name = models.CharField(max_length=100)
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    duration_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent_name', 'outcome']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.agent_name}: {self.outcome}'
