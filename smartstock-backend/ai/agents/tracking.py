"""Reusable lifecycle helper for AgentRun dashboard tracking.

Every agent execution should create an AgentRun record at start
and update it on completion/failure so the dashboard displays
real-time dynamic data.
"""

import logging

from django.utils import timezone

from apps.audit.models import AgentRun

logger = logging.getLogger(__name__)


def create_agent_run(agent_name: str) -> AgentRun:
    """Create a new AgentRun record with status=running.

    Returns the created AgentRun instance.
    """
    run = AgentRun.objects.create(
        agent_name=agent_name,
        status=AgentRun.Status.RUNNING,
        started_at=timezone.now(),
    )
    logger.debug('Created AgentRun %s for %s', run.id, agent_name)
    return run


def complete_agent_run(
    run_id: int,
    *,
    status: str = AgentRun.Status.COMPLETED,
    error_message: str = '',
) -> AgentRun | None:
    """Mark an AgentRun as completed or failed.

    Args:
        run_id: The AgentRun primary key.
        status: Final status (AgentRun.Status.COMPLETED or AgentRun.Status.FAILED).
        error_message: Optional error description for failed runs.

    Returns:
        The updated AgentRun instance, or None if not found.
    """
    try:
        run = AgentRun.objects.get(pk=run_id)
    except AgentRun.DoesNotExist:
        logger.warning('AgentRun %s not found — cannot complete', run_id)
        return None

    run.status = status
    run.completed_at = timezone.now()
    run.error_message = error_message
    run.save(update_fields=['status', 'completed_at', 'error_message', 'updated_at'])
    logger.debug('Completed AgentRun %s with status=%s', run_id, status)
    return run
