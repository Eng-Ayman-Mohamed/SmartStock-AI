import logging

from celery import shared_task

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

    logger.info("Starting purchasing workflow for context: %s", context)
    agent = PurchasingAgent()
    result = agent.run(context)
    logger.info("Purchasing workflow completed: %s", result.get("status"))
    return result


@shared_task
def run_purchasing_workflow_with_approval(
    context: dict, auto_approve: bool = False
) -> dict:
    """Execute the purchasing workflow, optionally skipping the HITL gate.

    Used for testing or integration scenarios where automatic approval is needed.
    """
    ctx = {**context, "auto_approve": auto_approve}
    return run_purchasing_workflow(ctx)
