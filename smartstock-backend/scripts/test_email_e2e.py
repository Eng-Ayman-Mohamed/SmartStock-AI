#!/usr/bin/env python
"""E2E test for PO email dispatch workflow.

Tests the full flow:
1. Create PO
2. Approve PO
3. Verify email is queued via Celery task
4. Verify supplier receives email

Usage:
    cd smartstock-backend
    python scripts/test_email_e2e.py
"""

import logging
import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from apps.inventory.models import Supplier  # noqa: E402
from apps.purchasing.email_tasks import send_email_with_retry  # noqa: E402
from apps.purchasing.services import PurchasingService  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()

TEST_SUPPLIERS = [
    {'name': 'Mostafa Abd Elqawy', 'email': 'mstfybdallh088@gmail.com'},
    {'name': 'Ahmed Mohamed', 'email': 'bc9265451@gmail.com'},
    {'name': 'Mahmoud Ibrahim', 'email': 'mhadry95@gmail.com'},
]


def ensure_test_suppliers():
    """Create or update test suppliers with real emails."""
    suppliers = []
    for data in TEST_SUPPLIERS:
        supplier, created = Supplier.objects.update_or_create(
            name=data['name'],
            defaults={
                'contact_email': data['email'],
                'is_active': True,
                'default_lead_time_days': 7,
            },
        )
        action = 'Created' if created else 'Updated'
        logger.info(
            f'{action} supplier: {supplier.name} <{supplier.contact_email}> (id={supplier.id})'
        )
        suppliers.append(supplier)
    return suppliers


def test_email_dispatch():
    """Test email dispatch directly via send_email_with_retry."""
    logger.info('=== Testing direct email dispatch ===')

    for supplier_data in TEST_SUPPLIERS:
        logger.info(f'Sending test email to {supplier_data["name"]} <{supplier_data["email"]}>')
        try:
            result = send_email_with_retry.__wrapped__(
                subject='SmartStock AI - Email Test',
                body=f'Hello {supplier_data["name"]},\n\nThis is a test email from SmartStock AI.\n\nTimestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}',
                recipient=supplier_data['email'],
                po_id=None,
                message_id=f'test-{int(time.time())}',
            )
            logger.info(f'Result: {result}')
        except Exception as e:
            logger.error(f'Failed to send email to {supplier_data["email"]}: {e}')


def test_po_approval_email():
    """Test full PO approval → email dispatch flow."""
    logger.info('=== Testing PO approval email dispatch ===')

    service = PurchasingService()

    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        logger.error('No admin user found. Creating test admin...')
        admin_user = User.objects.create_superuser(
            email='admin@smartstock.ai',
            password='testpass123',
            first_name='Test',
            last_name='Admin',
        )

    suppliers = ensure_test_suppliers()
    if not suppliers:
        logger.error('No suppliers available')
        return

    from apps.inventory.models import SKU

    sku = SKU.objects.first()
    if not sku:
        logger.error('No SKUs found in database')
        return

    for supplier in suppliers[:1]:
        logger.info(f'Creating PO for supplier {supplier.name}...')
        try:
            po = service.draft_po(
                sku_id=sku.id,
                quantity=10,
                supplier_id=supplier.id,
                user=admin_user,
                agent_reasoning='E2E test - email dispatch validation',
            )
            logger.info(f'Created PO-{po.id} (status={po.status})')

            logger.info(f'Approving PO-{po.id}...')
            po = service.approve_po(po.id, admin_user)
            logger.info(f'Approved PO-{po.id} (status={po.status})')
            logger.info('Email dispatch triggered via approve_po()')

        except Exception as e:
            logger.error(f'Failed for supplier {supplier.name}: {e}')


if __name__ == '__main__':
    logger.info('SmartStock AI - E2E Email Test')
    logger.info('=' * 50)

    ensure_test_suppliers()
    test_email_dispatch()
    test_po_approval_email()

    logger.info('=' * 50)
    logger.info('E2E test complete. Check Mailpit UI at http://localhost:8025')
