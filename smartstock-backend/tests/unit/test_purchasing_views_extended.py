"""Tests for apps/purchasing/views.py — approve, reject, overdue_suppliers, agent_workflow."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.inventory.models import SKU, Product, Supplier
from apps.purchasing.models import PurchaseOrder

User = get_user_model()


class SupplierViewSetPermissionsTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='sadmin', email='sa@test.com', password='pass1234', role='admin'
        )
        self.viewer = User.objects.create_user(
            username='sviewer', email='sv@test.com', password='pass1234', role='viewer'
        )
        self.client = APIClient()

    def test_viewer_can_list(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/purchasing/suppliers/')
        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_create(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post('/api/purchasing/suppliers/', {'name': 'Test'}, format='json')
        self.assertEqual(response.status_code, 403)


class PurchaseOrderViewSetActionsTest(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='pmgr', email='pm@test.com', password='pass1234', role='manager'
        )
        self.supplier = Supplier.objects.create(name='TestSupplier', is_active=True)
        product = Product.objects.create(name='TestProduct', is_active=True)
        self.sku = SKU.objects.create(product=product, code='SKU-TEST-001')
        self.po = PurchaseOrder.objects.create(
            sku=self.sku,
            quantity=10,
            supplier=self.supplier,
            requested_by=self.manager,
            status='pending',
            total_cost=Decimal('100.00'),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    @patch('apps.purchasing.views.PurchasingService')
    def test_approve_action(self, MockService):
        mock_service = MockService.return_value
        mock_service.approve_po.return_value = MagicMock(id=self.po.id)
        response = self.client.post(f'/api/purchasing/purchase-orders/{self.po.id}/approve/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved')

    @patch('apps.purchasing.views.PurchasingService')
    def test_reject_action(self, MockService):
        mock_service = MockService.return_value
        mock_service.reject_po.return_value = MagicMock(id=self.po.id)
        response = self.client.post(f'/api/purchasing/purchase-orders/{self.po.id}/reject/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'rejected')

    @patch('apps.purchasing.views.PurchasingService')
    def test_overdue_suppliers_action(self, MockService):
        mock_service = MockService.return_value
        mock_service.get_overdue_suppliers.return_value = []
        response = self.client.get('/api/purchasing/purchase-orders/overdue-suppliers/')
        self.assertEqual(response.status_code, 200)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_missing_fields(self, MockAgent):
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {'sku_id': 1},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_success(self, MockAgent):
        mock_agent = MockAgent.return_value
        mock_agent.run.return_value = {'status': 'completed', 'po_id': self.po.id}
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {
                'sku_id': self.sku.id,
                'quantity': 10,
                'supplier_id': self.supplier.id,
                'auto_approve': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_failed_returns_500(self, MockAgent):
        mock_agent = MockAgent.return_value
        mock_agent.run.return_value = {'status': 'failed', 'error': 'boom'}
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {
                'sku_id': self.sku.id,
                'quantity': 10,
                'supplier_id': self.supplier.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 500)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_pending_approval(self, MockAgent):
        mock_agent = MockAgent.return_value
        mock_agent.run.return_value = {'status': 'pending_approval'}
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {
                'sku_id': self.sku.id,
                'quantity': 10,
                'supplier_id': self.supplier.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 202)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_rejected(self, MockAgent):
        mock_agent = MockAgent.return_value
        mock_agent.run.return_value = {'status': 'rejected'}
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {
                'sku_id': self.sku.id,
                'quantity': 10,
                'supplier_id': self.supplier.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 409)

    @patch('ai.agents.purchasing_agent.PurchasingAgent')
    def test_agent_workflow_timeout(self, MockAgent):
        mock_agent = MockAgent.return_value
        mock_agent.run.return_value = {'status': 'timeout'}
        response = self.client.post(
            '/api/purchasing/purchase-orders/agent-workflow/',
            {
                'sku_id': self.sku.id,
                'quantity': 10,
                'supplier_id': self.supplier.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 408)
