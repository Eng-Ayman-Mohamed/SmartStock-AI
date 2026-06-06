
from .models import AuditLog

def log_ai_action(event: str, user, entity_type: str = '', entity_id: int = None, data: dict = None, ip: str = None):
    """
    Convenience function called directly from AI views/services.
    Events: AI_NL_QUERY, AI_RAG_QUERY, AI_INVOICE_SCAN, AI_VOICE_TRANSCRIBE
    """
    AuditLog.objects.create(
        event=event,
        entity_type=entity_type,
        entity_id=entity_id,
        user=user,
        ip_address=ip,
        data=data or {},
    )