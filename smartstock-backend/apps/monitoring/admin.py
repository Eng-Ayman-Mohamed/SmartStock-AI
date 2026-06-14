from django.contrib import admin

from .models import AgentRunLog, AlertEvent, AlertRule, DashboardBanner, TokenUsageLog


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity', 'metric_name', 'threshold', 'enabled', 'cooldown_minutes')
    list_filter = ('severity', 'enabled')
    search_fields = ('name',)


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = (
        'rule',
        'status',
        'triggered_value',
        'email_sent',
        'dashboard_notified',
        'created_at',
    )
    list_filter = ('status', 'rule')
    search_fields = ('message',)


@admin.register(DashboardBanner)
class DashboardBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'dismissed', 'created_at')
    list_filter = ('level', 'dismissed')


@admin.register(TokenUsageLog)
class TokenUsageLogAdmin(admin.ModelAdmin):
    list_display = ('total_tokens', 'input_tokens', 'output_tokens', 'logged_at')
    list_filter = ('logged_at',)


@admin.register(AgentRunLog)
class AgentRunLogAdmin(admin.ModelAdmin):
    list_display = ('agent_name', 'outcome', 'duration_ms', 'created_at')
    list_filter = ('outcome', 'agent_name')
