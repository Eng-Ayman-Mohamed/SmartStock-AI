from decimal import Decimal

from django.test import TestCase

from apps.authentication.models import CustomUser
from apps.inventory.models import Category, Product, SKU, Supplier
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.repositories import PurchasingRepository


class PurchasingRepositoryTest(TestCase):
    def setUp(self):
        self.repo = PurchasingRepository()

        self.user = CustomUser.objects.create_user(
            username='repo_test_user',
            email='repo@test.com',
            password='pass123',
            role='manager',
        )
        self.category = Category.objects.create(name='Repo Test Cat')
        self.product = Product.objects.create(
            name='Repo Test Product',
            category=self.category,
        )
        self.sku = SKU.objects.create(product=self.product, code='REPO-SKU-001')
        self.supplier = Supplier.objects.create(
            name='Repo Test Supplier',
            contact_email='repo@supplier.com',
            default_lead_time_days=10,
        )

    def _create_po(self, status='draft', **overrides):
        defaults = {
            'sku': self.sku,
            'supplier': self.supplier,
            'quantity': 50,
            'total_cost': Decimal('500.00'),
            'status': status,
            'requested_by': self.user,
        }
        defaults.update(overrides)
        return PurchaseOrder.objects.create(**defaults)


class PurchasingRepositoryGetByIdTest(PurchasingRepositoryTest):
    def test_get_by_id_returns_correct_po(self):
        po = self._create_po()
        result = self.repo.get_by_id(po.id)
        self.assertEqual(result.id, po.id)
        self.assertEqual(result.sku.code, 'REPO-SKU-001')

    def test_get_by_id_nonexistent_raises(self):
        from django.core.exceptions import ObjectDoesNotExist

        with self.assertRaises(ObjectDoesNotExist):
            self.repo.get_by_id(99999)


class PurchasingRepositoryGetAllTest(PurchasingRepositoryTest):
    def test_get_all_empty(self):
        result = self.repo.get_all()
        self.assertEqual(result.count(), 0)

    def test_get_all_returns_all_pos(self):
        po1 = self._create_po()
        po2 = self._create_po(quantity=10, total_cost=Decimal('100.00'))
        result = self.repo.get_all()
        self.assertEqual(result.count(), 2)
        ids = set(result.values_list('id', flat=True))
        self.assertIn(po1.id, ids)
        self.assertIn(po2.id, ids)

    def test_get_all_returns_queryset(self):
        from django.db.models import QuerySet

        result = self.repo.get_all()
        self.assertIsInstance(result, QuerySet)


class PurchasingRepositoryGetOpenForProductTest(PurchasingRepositoryTest):
    def _create_product_with_sku(self, product_id_suffix='A'):
        product = Product.objects.create(
            name=f'Product {product_id_suffix}',
            category=self.category,
        )
        sku = SKU.objects.create(product=product, code=f'OPEN-SKU-{product_id_suffix}')
        return product, sku

    def test_no_open_po_returns_none(self):
        product, sku = self._create_product_with_sku('X')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNone(result)

    def test_draft_po_is_open(self):
        product, sku = self._create_product_with_sku('D')
        po = self._create_po(sku=sku)
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, po.id)

    def test_sent_po_is_open(self):
        product, sku = self._create_product_with_sku('S')
        po = self._create_po(sku=sku, status='sent')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, po.id)

    def test_approved_po_is_open(self):
        product, sku = self._create_product_with_sku('A')
        po = self._create_po(sku=sku, status='approved')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNotNone(result)

    def test_pending_approval_po_is_open(self):
        product, sku = self._create_product_with_sku('P')
        po = self._create_po(sku=sku, status='pending_approval')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNotNone(result)

    def test_rejected_po_is_not_open(self):
        product, sku = self._create_product_with_sku('R')
        self._create_po(sku=sku, status='rejected')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNone(result)

    def test_cancelled_po_is_not_open(self):
        product, sku = self._create_product_with_sku('C')
        self._create_po(sku=sku, status='cancelled')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNone(result)

    def test_confirmed_po_is_not_open(self):
        product, sku = self._create_product_with_sku('F')
        self._create_po(sku=sku, status='confirmed')
        result = self.repo.get_open_for_product(product.id)
        self.assertIsNone(result)

    def test_returns_most_recent_open_po(self):
        product, sku = self._create_product_with_sku('M')
        old_po = self._create_po(sku=sku, quantity=10)
        new_po = self._create_po(sku=sku, quantity=20)
        result = self.repo.get_open_for_product(product.id)
        self.assertEqual(result.id, new_po.id)

    def test_only_checks_pos_for_given_product(self):
        product_a, sku_a = self._create_product_with_sku('A1')
        product_b, sku_b = self._create_product_with_sku('B1')
        po_a = self._create_po(sku=sku_a)
        result = self.repo.get_open_for_product(product_b.id)
        self.assertIsNone(result)


class PurchasingRepositoryCreateTest(PurchasingRepositoryTest):
    def test_create_po(self):
        data = {
            'sku': self.sku,
            'supplier': self.supplier,
            'quantity': 75,
            'total_cost': Decimal('750.00'),
            'requested_by': self.user,
            'status': 'draft',
        }
        result = self.repo.create(data)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.quantity, 75)
        self.assertEqual(result.total_cost, Decimal('750.00'))
        self.assertEqual(result.status, 'draft')
        self.assertEqual(result.sku, self.sku)
        self.assertEqual(result.supplier, self.supplier)

    def test_create_po_persists_to_db(self):
        data = {
            'sku': self.sku,
            'supplier': self.supplier,
            'quantity': 1,
            'total_cost': Decimal('10.00'),
            'status': 'draft',
        }
        result = self.repo.create(data)
        self.assertTrue(PurchaseOrder.objects.filter(pk=result.id).exists())

    def test_create_po_with_notes(self):
        data = {
            'sku': self.sku,
            'supplier': self.supplier,
            'quantity': 5,
            'total_cost': Decimal('50.00'),
            'status': 'draft',
            'notes': 'Urgent order',
        }
        result = self.repo.create(data)
        self.assertEqual(result.notes, 'Urgent order')


class PurchasingRepositoryUpdateTest(PurchasingRepositoryTest):
    def test_update_status(self):
        po = self._create_po()
        result = self.repo.update(po.id, {'status': 'approved'})
        self.assertEqual(result.status, 'approved')

    def test_update_quantity(self):
        po = self._create_po()
        result = self.repo.update(po.id, {'quantity': 999})
        self.assertEqual(result.quantity, 999)

    def test_update_multiple_fields(self):
        po = self._create_po()
        result = self.repo.update(
            po.id,
            {
                'status': 'sent',
                'notes': 'Shipped today',
            },
        )
        self.assertEqual(result.status, 'sent')
        self.assertEqual(result.notes, 'Shipped today')

    def test_update_returns_fresh_instance(self):
        po = self._create_po()
        result = self.repo.update(po.id, {'quantity': 42})
        self.assertEqual(result.quantity, 42)
        fresh = PurchaseOrder.objects.get(pk=po.id)
        self.assertEqual(fresh.quantity, 42)

    def test_update_does_not_touch_other_records(self):
        po1 = self._create_po(quantity=10)
        po2 = self._create_po(quantity=20)
        self.repo.update(po1.id, {'quantity': 100})
        po2.refresh_from_db()
        self.assertEqual(po2.quantity, 20)


class PurchasingRepositoryDeleteTest(PurchasingRepositoryTest):
    def test_delete_removes_po(self):
        po = self._create_po()
        self.repo.delete(po.id)
        self.assertFalse(PurchaseOrder.objects.filter(pk=po.id).exists())

    def test_delete_only_removes_specified(self):
        po1 = self._create_po()
        po2 = self._create_po(quantity=10)
        self.repo.delete(po1.id)
        self.assertFalse(PurchaseOrder.objects.filter(pk=po1.id).exists())
        self.assertTrue(PurchaseOrder.objects.filter(pk=po2.id).exists())
