import logging
import uuid

from ai.agents.base_agent import BaseTool
from apps.purchasing.email_tasks import send_email_with_retry
from apps.purchasing.services import PurchasingService

logger = logging.getLogger(__name__)


class EmailSendTool(BaseTool):
    name = 'email_send_tool'
    description = 'Dispatches an approved Purchase Order to the supplier via email.'

    def __init__(self, purchasing_service=None, email_service=None):
        self.purchasing_service = purchasing_service or PurchasingService()

    def run(self, input: dict) -> dict:
        try:
            po_id = int(input['po_id'])
            po = self.purchasing_service.repo.get_by_id(po_id)

            if po.status not in ('approved', 'sent'):
                return {
                    'status': 'failed',
                    'error': f'PO-{po_id} is not in approved/sent status (current: {po.status})',
                }

            recipient_email = input.get('recipient_email')
            supplier_name = input.get('supplier_name', '')
            if not recipient_email:
                supplier = po.supplier
                recipient_email = supplier.contact_email
                supplier_name = supplier.name

            sku_code = po.sku.code
            product_name = po.sku.product.name
            subject = f'Purchase Order PO-{po_id} - {sku_code}'
            body = self._build_email_body(
                po_id,
                sku_code,
                product_name,
                po.quantity,
                po.total_cost,
                po.requested_by,
                supplier_name,
            )

            message_id = f'po-{po_id}-{uuid.uuid4().hex[:8]}'

            task_result = send_email_with_retry.delay(
                subject=subject,
                body=body,
                recipient=recipient_email,
                po_id=po_id,
                message_id=message_id,
            )

            logger.info(
                'PO email dispatch queued: PO-%s to %s (message_id=%s, task_id=%s)',
                po_id,
                recipient_email,
                message_id,
                task_result.id,
            )
            return {
                'status': 'sent',
                'po_id': po_id,
                'message_id': message_id,
                'recipient': recipient_email,
                'task_id': task_result.id,
            }
        except Exception as e:
            logger.exception('EmailSendTool failed for PO-%s', input.get('po_id'))
            return {'status': 'failed', 'error': str(e)}

    def _build_email_body(
        self,
        po_id,
        sku_code,
        product_name,
        quantity,
        total_cost,
        requested_by,
        supplier_name,
    ) -> str:
        return (
            f'Purchase Order PO-{po_id}\n'
            f'================================\n\n'
            f'Supplier: {supplier_name}\n'
            f'SKU: {sku_code}\n'
            f'Product: {product_name}\n'
            f'Quantity: {quantity}\n'
            f'Total Cost: ${total_cost}\n'
            f'Requested By: {requested_by}\n\n'
            f'Please confirm receipt of this order.\n\n'
            f'Regards,\nSmartStock AI Purchasing Agent'
        )
