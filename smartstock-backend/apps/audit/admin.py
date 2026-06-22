from django.contrib import admin

from .models import AgentRun, AuditLog


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ('agent_name', 'status', 'started_at', 'completed_at', 'created_at')
    list_filter = ('status', 'agent_name')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(AuditLog)
