import logging

from celery import shared_task

from . import timeout_tasks  # noqa: F401 — ensure timeout tasks are registered with Celery

logger = logging.getLogger(__name__)


@shared_task
def run_purchasing_workflow(context: dict) -> dict:
    """Execute the purchasing agent workflow asynchronously via Celery.

    Args:
        context: dict with keys sku_id, quantity, supplier_id, user_id, etc.

    Returns:
        dict with workflow result.
    """
    from ai.agents.purchasing_agent import PurchasingAgent

    logger.info('Starting purchasing workflow for context: %s', context)
    agent = PurchasingAgent()
    result = agent.run(context)
    logger.info('Purchasing workflow completed: %s', result.get('status'))
    return result


@shared_task
def run_purchasing_workflow_with_approval(context: dict, auto_approve: bool = False) -> dict:
    """Execute the purchasing workflow, optionally skipping the HITL gate.

    Used for testing or integration scenarios where automatic approval is needed.
    """
    ctx = {**context, 'auto_approve': auto_approve}
    return run_purchasing_workflow(ctx)


@shared_task
def check_overdue_suppliers():
    """Check for suppliers with overdue POs and create notification records."""
    from apps.notifications.models import Notification
    from apps.notifications.service import NotificationService
    from apps.purchasing.services import PurchasingService

    overdue = PurchasingService().get_overdue_suppliers()

    if not overdue:
        return {'created': 0}

    created = 0
    for supplier in overdue:
        # Deduplicate: skip if a notification for this supplier already exists today
        existing = Notification.objects.filter(
            type='escalation',
            metadata__supplier_id=supplier['supplier_id'],
            title__startswith='Supplier non-response:',
        ).exists()
        if existing:
            continue

        po_numbers = ', '.join(po['po_number'] for po in supplier['overdue_pos'])
        NotificationService.create(
            type='escalation',
            severity='warning',
            title=f'Supplier non-response: {supplier["supplier_name"]}',
            message=(
                f'{supplier["supplier_name"]} has not responded within the expected timeframe. '
                f'Overdue by {supplier["days_overdue"]} day(s). '
                f'POs: {po_numbers}'
            ),
            metadata={
                'supplier_id': supplier['supplier_id'],
                'supplier_name': supplier['supplier_name'],
                'days_overdue': supplier['days_overdue'],
                'overdue_pos': supplier['overdue_pos'],
                'source': 'overdue_supplier_check',
            },
        )
        created += 1

    logger.info('Created %d overdue supplier notifications', created)
    return {'created': created}
