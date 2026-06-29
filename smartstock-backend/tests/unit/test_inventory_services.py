from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.inventory.services import (
    InventoryService,
    SalesRecordService,
    SKUService,
    _invalidate_product_cache,
    get_product_cache_version,
)
from core.exceptions import StockNotFoundException

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class InvalidateProductCacheTest(TestCase):
    @patch('apps.inventory.services.cache')
    def test_increments_version(self, mock_cache):
        initial = get_product_cache_version()
        _invalidate_product_cache()
        self.assertEqual(get_product_cache_version(), initial + 1)

    @patch('apps.inventory.services.cache')
    def test_deletes_cache_keys(self, mock_cache):
        _invalidate_product_cache()
        mock_cache.delete_pattern.assert_called_with('product_list_*')
        mock_cache.delete.assert_called_with('low_stock_items')


class GetProductCacheVersionTest(TestCase):
    @patch('apps.inventory.services.cache')
    def test_returns_int(self, self2=None):
        self.assertIsInstance(get_product_cache_version(), int)


# ---------------------------------------------------------------------------
# InventoryService
# ---------------------------------------------------------------------------


class InventoryServiceInitTest(TestCase):
    def test_default_repos_created(self):
        svc = InventoryService()
        self.assertIsNotNone(svc.repo)
        self.assertIsNotNone(svc.stock_repo)
        self.assertIsNotNone(svc.cat_repo)
        self.assertIsNotNone(svc.sku_repo)
        self.assertIsNotNone(svc.supplier_repo)

    def test_custom_repos_injected(self):
        repo = MagicMock()
        stock_repo = MagicMock()
        cat_repo = MagicMock()
        sku_repo = MagicMock()
        supplier_repo = MagicMock()
        svc = InventoryService(
            repo=repo,
            stock_repo=stock_repo,
            cat_repo=cat_repo,
            sku_repo=sku_repo,
            supplier_repo=supplier_repo,
        )
        self.assertIs(svc.repo, repo)
        self.assertIs(svc.stock_repo, stock_repo)
        self.assertIs(svc.cat_repo, cat_repo)
        self.assertIs(svc.sku_repo, sku_repo)
        self.assertIs(svc.supplier_repo, supplier_repo)


class InventoryServiceGetAllProductsTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.svc = InventoryService(repo=self.repo)

    def test_delegates_to_repo(self):
        self.svc.get_all_products()
        self.repo.get_all.assert_called_once_with(include_inactive=False)

    def test_include_inactive(self):
        self.svc.get_all_products(include_inactive=True)
        self.repo.get_all.assert_called_once_with(include_inactive=True)


class InventoryServiceGetProductTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.svc = InventoryService(repo=self.repo)

    def test_delegates_to_repo(self):
        self.svc.get_product(42)
        self.repo.get_by_id.assert_called_once_with(42)


class InventoryServiceCreateProductTest(TestCase):
    @patch('apps.inventory.services._invalidate_product_cache')
    def test_creates_and_invalidates(self, mock_inv):
        repo = MagicMock()
        svc = InventoryService(repo=repo)
        data = {'name': 'Widget'}
        result = svc.create_product(data)
        repo.create.assert_called_once_with(data)
        mock_inv.assert_called_once()
        self.assertEqual(result, repo.create.return_value)


class InventoryServiceUpdateProductTest(TestCase):
    @patch('apps.inventory.services._invalidate_product_cache')
    def test_updates_and_invalidates(self, mock_inv):
        repo = MagicMock()
        svc = InventoryService(repo=repo)
        data = {'name': 'Updated'}
        result = svc.update_product(10, data)
        repo.update.assert_called_once_with(10, data)
        mock_inv.assert_called_once()
        self.assertEqual(result, repo.update.return_value)


class InventoryServiceDeleteProductTest(TestCase):
    @patch('apps.inventory.services._invalidate_product_cache')
    def test_soft_deletes_and_invalidates(self, mock_inv):
        repo = MagicMock()
        svc = InventoryService(repo=repo)
        svc.delete_product(5)
        repo.soft_delete.assert_called_once_with(5)
        mock_inv.assert_called_once()


class InventoryServiceFindStockForProductTest(TestCase):
    def test_delegates_to_stock_repo(self):
        stock_repo = MagicMock()
        svc = InventoryService(stock_repo=stock_repo)
        svc.find_stock_for_product(3)
        stock_repo.get_by_product_id.assert_called_once_with(3)


# ---------------------------------------------------------------------------
# get_decision_stock_data
# ---------------------------------------------------------------------------


class GetDecisionStockDataTest(TestCase):
    def setUp(self):
        self.stock_repo = MagicMock()
        self.svc = InventoryService(stock_repo=self.stock_repo)

    def _make_stock(self, reorder_point=5, lead_time_days=10):
        supplier = MagicMock(default_lead_time_days=lead_time_days)
        product = MagicMock(id=1, reorder_point=10, safety_stock=3, supplier=supplier)
        sku = MagicMock(code='SKU-001', product=product)
        stock = MagicMock(sku=sku, quantity_available=20, reorder_point=reorder_point)
        return stock

    def test_returns_correct_dict(self):
        stock = self._make_stock()
        self.stock_repo.get_by_product_id.return_value = stock
        result = self.svc.get_decision_stock_data(1)
        self.assertEqual(result['product_id'], 1)
        self.assertEqual(result['sku_code'], 'SKU-001')
        self.assertEqual(result['quantity_available'], 20)
        self.assertEqual(result['lead_time_days'], 10)
        self.assertEqual(result['safety_stock'], 3)

    def test_falls_back_to_product_reorder_point(self):
        stock = self._make_stock(reorder_point=None)
        self.stock_repo.get_by_product_id.return_value = stock
        result = self.svc.get_decision_stock_data(1)
        self.assertEqual(result['reorder_point'], 10)

    def test_falls_back_to_default_lead_time(self):
        stock = self._make_stock()
        stock.sku.product.supplier.default_lead_time_days = None
        self.stock_repo.get_by_product_id.return_value = stock
        result = self.svc.get_decision_stock_data(1)
        self.assertEqual(result['lead_time_days'], 7)

    def test_raises_when_no_stock(self):
        self.stock_repo.get_by_product_id.return_value = None
        with self.assertRaises(StockNotFoundException):
            self.svc.get_decision_stock_data(999)


class GetDecisionStockDataBySkuTest(TestCase):
    def setUp(self):
        self.stock_repo = MagicMock()
        self.svc = InventoryService(stock_repo=self.stock_repo)

    def _make_stock(self, reorder_point=5, lead_time_days=10):
        supplier = MagicMock(default_lead_time_days=lead_time_days)
        product = MagicMock(id=1, reorder_point=10, safety_stock=3, supplier=supplier)
        sku = MagicMock(id=42, code='SKU-042', product=product)
        stock = MagicMock(sku=sku, sku_id=42, quantity_available=15, reorder_point=reorder_point)
        return stock

    def test_returns_correct_dict(self):
        stock = self._make_stock()
        self.stock_repo.get_by_sku_id.return_value = stock
        result = self.svc.get_decision_stock_data_by_sku(42)
        self.assertEqual(result['sku_id'], 42)
        self.assertEqual(result['sku_code'], 'SKU-042')
        self.assertEqual(result['product_id'], 1)
        self.assertEqual(result['quantity_available'], 15)
        self.assertEqual(result['reorder_point'], 5)
        self.assertEqual(result['lead_time_days'], 10)
        self.assertEqual(result['safety_stock'], 3)

    def test_falls_back_to_product_reorder_point(self):
        stock = self._make_stock(reorder_point=None)
        self.stock_repo.get_by_sku_id.return_value = stock
        result = self.svc.get_decision_stock_data_by_sku(42)
        self.assertEqual(result['reorder_point'], 10)

    def test_falls_back_to_default_lead_time(self):
        stock = self._make_stock()
        stock.sku.product.supplier.default_lead_time_days = None
        self.stock_repo.get_by_sku_id.return_value = stock
        result = self.svc.get_decision_stock_data_by_sku(42)
        self.assertEqual(result['lead_time_days'], 7)

    def test_raises_when_no_stock(self):
        self.stock_repo.get_by_sku_id.return_value = None
        with self.assertRaises(StockNotFoundException):
            self.svc.get_decision_stock_data_by_sku(999)


# ---------------------------------------------------------------------------
# get_low_stock_items
# ---------------------------------------------------------------------------


class GetLowStockItemsTest(TestCase):
    def setUp(self):
        self.stock_repo = MagicMock()
        self.svc = InventoryService(stock_repo=self.stock_repo)

    def _make_stock_level(self, sku_id, qty, reorder_point=10):
        supplier = MagicMock(name='Acme Corp')
        product = MagicMock(id=100 + sku_id, name=f'Product {sku_id}', supplier=supplier)
        sku = MagicMock(id=sku_id, code=f'SKU-{sku_id}', product=product)
        return MagicMock(
            id=sku_id, sku=sku, sku_id=sku_id, quantity_on_hand=qty, reorder_point=reorder_point
        )

    @patch('apps.inventory.services.cache')
    def test_returns_cached_result_when_available(self, mock_cache):
        cached = [{'id': 1}]
        mock_cache.get.return_value = cached
        result = self.svc.get_low_stock_items()
        self.assertEqual(result, cached)
        self.stock_repo.get_low_stock.assert_not_called()

    @patch('apps.inventory.models.SalesRecord')
    @patch('apps.inventory.services.cache')
    @patch('django.utils.timezone')
    def test_returns_empty_when_no_low_stock(self, mock_tz, mock_cache, mock_sr):
        mock_cache.get.return_value = None
        self.stock_repo.get_low_stock.return_value = []
        result = self.svc.get_low_stock_items()
        self.assertEqual(result, [])
        mock_cache.set.assert_called_once()

    @patch('apps.inventory.models.SalesRecord')
    @patch('apps.inventory.services.cache')
    @patch('django.utils.timezone')
    def test_no_demand_leaves_predicted_stockout_none(self, mock_tz, mock_cache, mock_sr):
        mock_cache.get.return_value = None
        sl = self._make_stock_level(1, 5)
        self.stock_repo.get_low_stock.return_value = [sl]
        mock_tz.localdate.return_value = __import__('datetime').date(2026, 1, 15)

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.values.return_value = qs
        qs.annotate.return_value = qs
        qs.values_list.return_value = []
        mock_sr.objects.filter.return_value = qs

        result = self.svc.get_low_stock_items()
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]['predicted_stockout_date'])

    @patch('apps.inventory.models.SalesRecord')
    @patch('apps.inventory.services.cache')
    @patch('django.utils.timezone')
    def test_with_demand_calculates_stockout(self, mock_tz, mock_cache, mock_sr):
        mock_cache.get.return_value = None
        sl = self._make_stock_level(1, 30)
        self.stock_repo.get_low_stock.return_value = [sl]
        mock_tz.localdate.return_value = __import__('datetime').date(2026, 1, 15)

        qs = MagicMock()
        qs.filter.return_value = qs
        qs.values.return_value = qs
        qs.annotate.return_value = qs
        qs.values_list.return_value = [(1, 60)]
        mock_sr.objects.filter.return_value = qs

        result = self.svc.get_low_stock_items()
        self.assertEqual(len(result), 1)
        self.assertIsNotNone(result[0]['predicted_stockout_date'])


# ---------------------------------------------------------------------------
# filter_by_stock_status
# ---------------------------------------------------------------------------


class FilterByStockStatusTest(TestCase):
    def test_in_stock_filter(self):
        qs = MagicMock()
        qs.annotate.return_value = qs
        qs.filter.return_value = qs
        result = InventoryService.filter_by_stock_status(qs, 'in_stock')
        self.assertEqual(result, qs)
        qs.annotate.assert_called_once()
        qs.filter.assert_called_once()

    def test_low_stock_filter(self):
        qs = MagicMock()
        qs.annotate.return_value = qs
        qs.filter.return_value = qs
        result = InventoryService.filter_by_stock_status(qs, 'low_stock')
        self.assertEqual(result, qs)

    def test_out_of_stock_filter(self):
        qs = MagicMock()
        qs.annotate.return_value = qs
        qs.filter.return_value = qs
        result = InventoryService.filter_by_stock_status(qs, 'out_of_stock')
        self.assertEqual(result, qs)

    def test_unknown_value_returns_unfiltered(self):
        qs = MagicMock()
        qs.annotate.return_value = qs
        InventoryService.filter_by_stock_status(qs, 'unknown')
        qs.annotate.assert_called_once()
        qs.filter.assert_not_called()


# ---------------------------------------------------------------------------
# adjust_stock
# ---------------------------------------------------------------------------


class AdjustStockTest(TestCase):
    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.stock_adjusted')
    def test_adjusts_and_sends_signal(self, mock_signal, mock_inv):
        repo = MagicMock()
        svc = InventoryService(repo=repo)
        stock = MagicMock()
        repo.adjust_stock.return_value = stock
        user = MagicMock()
        result = svc.adjust_stock(7, 5, user=user, reason='restock')
        repo.adjust_stock.assert_called_once_with(7, 5)
        mock_inv.assert_called_once()
        mock_signal.send.assert_called_once_with(
            sender=svc,
            stock_level=stock,
            delta=5,
            user=user,
            reason='restock',
        )
        self.assertEqual(result, stock)

    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.stock_adjusted')
    def test_adjust_stock_with_defaults(self, mock_signal, mock_inv):
        repo = MagicMock()
        svc = InventoryService(repo=repo)
        stock = MagicMock()
        repo.adjust_stock.return_value = stock
        svc.adjust_stock(1, -3)
        mock_signal.send.assert_called_once_with(
            sender=svc,
            stock_level=stock,
            delta=-3,
            user=None,
            reason='',
        )


# ---------------------------------------------------------------------------
# apply_confirmed_invoice
# ---------------------------------------------------------------------------


class ApplyConfirmedInvoiceTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.stock_repo = MagicMock()
        self.sku_repo = MagicMock()
        self.supplier_repo = MagicMock()
        self.svc = InventoryService(
            repo=self.repo,
            stock_repo=self.stock_repo,
            sku_repo=self.sku_repo,
            supplier_repo=self.supplier_repo,
        )

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_existing_sku_existing_stock(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        result = self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'sku-a',
                'product_name': 'Widget',
                'quantity_received': '5',
                'unit_price': '9.99',
                'supplier_name': 'Acme',
            }
        )

        self.assertEqual(result['quantity_added'], 5)
        self.stock_repo.update.assert_called_once()

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_existing_sku_no_stock(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = None
        self.stock_repo.create.return_value = MagicMock(id=40, quantity_on_hand=5)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        result = self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'SKU-A',
                'product_name': 'Widget',
                'quantity_received': '5',
            }
        )
        self.stock_repo.create.assert_called_once()
        self.assertEqual(result['quantity_added'], 5)

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_new_sku_creates_product_sku_stock(self, mock_inv):
        self.sku_repo.get_by_code.return_value = None
        product = MagicMock(id=50)
        self.repo.create.return_value = product
        self.sku_repo.create.return_value = MagicMock(id=60, code='NEW-SKU')
        self.stock_repo.create.return_value = MagicMock(id=70, quantity_on_hand=10)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'NEW-SKU',
                'product_name': 'New Product',
                'quantity_received': '10',
                'unit_price': '5.00',
                'supplier_name': 'Acme',
            }
        )
        self.repo.create.assert_called_once()
        self.sku_repo.create.assert_called_once()
        self.stock_repo.create.assert_called_once()

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_updates_unit_price_and_supplier(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)
        supplier = MagicMock()
        self.supplier_repo.get_by_name.return_value = supplier

        self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'SKU-A',
                'product_name': 'Widget',
                'quantity_received': '5',
                'unit_price': '12.50',
                'supplier_name': 'Acme',
            }
        )
        self.repo.update.assert_called_once_with(
            20, {'unit_price': Decimal('12.50'), 'supplier': supplier}
        )

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_no_supplier_name_skips_supplier_lookup(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)

        self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'SKU-A',
                'product_name': 'Widget',
                'quantity_received': '5',
                'supplier_name': '',
            }
        )
        self.supplier_repo.get_by_name.assert_not_called()
        self.repo.update.assert_not_called()

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_empty_supplier_treated_as_no_supplier(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)

        self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'SKU-A',
                'product_name': 'Widget',
                'quantity_received': '5',
                'supplier_name': '  ',
            }
        )
        self.supplier_repo.get_by_name.assert_not_called()

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_unit_price_none_does_not_update_price(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.sku_repo.get_by_code.return_value = sku
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)

        self.svc.apply_confirmed_invoice(
            {
                'sku_code': 'SKU-A',
                'product_name': 'Widget',
                'quantity_received': '5',
            }
        )
        self.repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# apply_confirmed_invoice_lines
# ---------------------------------------------------------------------------


class ApplyConfirmedInvoiceLinesTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.stock_repo = MagicMock()
        self.sku_repo = MagicMock()
        self.supplier_repo = MagicMock()
        self.svc = InventoryService(
            repo=self.repo,
            stock_repo=self.stock_repo,
            sku_repo=self.sku_repo,
            supplier_repo=self.supplier_repo,
        )

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_all_lines_succeed(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        self.sku_repo.get_by_code.return_value = sku
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        result = self.svc.apply_confirmed_invoice_lines(
            header={'supplier_name': 'Acme'},
            line_items=[
                {'item_name': 'Widget', 'sku_code': 'SKU-A', 'quantity': '5', 'unit_price': '9.99'},
                {'item_name': 'Gadget', 'sku_code': 'SKU-B', 'quantity': '3', 'unit_price': '4.50'},
            ],
        )
        self.assertEqual(result['lines_processed'], 2)
        self.assertEqual(len(result['lines_failed']), 0)

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_one_line_fails_validation(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        self.sku_repo.get_by_code.return_value = sku
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        def fake_apply(data, user=None):
            if data.get('sku_code') == 'BAD-SKU':
                raise ValidationError('Invalid SKU')
            return {
                'product_id': 20,
                'sku_id': 10,
                'stock_level_id': 30,
                'quantity_added': 5,
                'quantity_on_hand': 15,
            }

        self.svc.apply_confirmed_invoice = fake_apply

        result = self.svc.apply_confirmed_invoice_lines(
            header={'supplier_name': 'Acme'},
            line_items=[
                {'item_name': 'Widget', 'sku_code': 'SKU-A', 'quantity': '5', 'unit_price': '9.99'},
                {'item_name': 'Bad', 'sku_code': 'BAD-SKU', 'quantity': '1'},
            ],
        )
        self.assertEqual(result['lines_processed'], 1)
        self.assertEqual(len(result['lines_failed']), 1)
        self.assertEqual(result['lines_failed'][0]['sku_code'], 'BAD-SKU')

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_all_lines_fail_raises(self, mock_inv):
        def fake_apply(data, user=None):
            raise ValidationError('Invalid')

        self.svc.apply_confirmed_invoice = fake_apply

        with self.assertRaises(ValidationError) as ctx:
            self.svc.apply_confirmed_invoice_lines(
                header={'supplier_name': 'Acme'},
                line_items=[
                    {'item_name': 'Bad1', 'sku_code': 'BAD-1', 'quantity': '1'},
                    {'item_name': 'Bad2', 'sku_code': 'BAD-2', 'quantity': '2'},
                ],
            )
        self.assertIn('No invoice line items could be applied', str(ctx.exception))

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_empty_line_items(self, mock_inv):
        result = self.svc.apply_confirmed_invoice_lines(
            header={'supplier_name': 'Acme'},
            line_items=[],
        )
        self.assertEqual(result['lines_processed'], 0)
        self.assertEqual(result['lines_failed'], [])

    @patch('apps.inventory.services._invalidate_product_cache')
    def test_line_result_includes_item_name_and_sku_code(self, mock_inv):
        sku = MagicMock(id=10, code='SKU-A', product=MagicMock(id=20))
        self.sku_repo.get_by_code.return_value = sku
        stock = MagicMock(id=30, quantity_on_hand=10, sku_id=10)
        self.stock_repo.get_by_sku_id.return_value = stock
        self.stock_repo.update.return_value = MagicMock(quantity_on_hand=15, id=30)
        self.supplier_repo.get_by_name.return_value = MagicMock()

        result = self.svc.apply_confirmed_invoice_lines(
            header={'supplier_name': 'Acme'},
            line_items=[
                {'item_name': 'Widget', 'sku_code': 'SKU-A', 'quantity': '5'},
            ],
        )
        line = result['lines'][0]
        self.assertEqual(line['item_name'], 'Widget')
        self.assertEqual(line['sku_code'], 'SKU-A')


# ---------------------------------------------------------------------------
# Category / StockLevel / Supplier CRUD
# ---------------------------------------------------------------------------


class CategoryServiceMethodsTest(TestCase):
    def setUp(self):
        self.cat_repo = MagicMock()
        self.svc = InventoryService(cat_repo=self.cat_repo)

    def test_get_all_categories(self):
        self.svc.get_all_categories()
        self.cat_repo.get_all.assert_called_once()

    def test_get_category(self):
        self.svc.get_category(3)
        self.cat_repo.get_by_id.assert_called_once_with(3)


class StockLevelServiceMethodsTest(TestCase):
    def setUp(self):
        self.stock_repo = MagicMock()
        self.svc = InventoryService(stock_repo=self.stock_repo)

    def test_get_all_stock_levels(self):
        self.svc.get_all_stock_levels()
        self.stock_repo.get_all.assert_called_once()

    def test_get_stock_level(self):
        self.svc.get_stock_level(7)
        self.stock_repo.get_by_id.assert_called_once_with(7)

    def test_create_stock_level(self):
        data = {'quantity_on_hand': 10}
        self.svc.create_stock_level(data)
        self.stock_repo.create.assert_called_once_with(data)

    def test_update_stock_level(self):
        data = {'quantity_on_hand': 20}
        self.svc.update_stock_level(7, data)
        self.stock_repo.update.assert_called_once_with(7, data)

    def test_delete_stock_level(self):
        self.svc.delete_stock_level(7)
        self.stock_repo.delete.assert_called_once_with(7)


class SupplierServiceMethodsTest(TestCase):
    def setUp(self):
        self.supplier_repo = MagicMock()
        self.svc = InventoryService(supplier_repo=self.supplier_repo)

    def test_get_all_suppliers(self):
        self.svc.get_all_suppliers()
        self.supplier_repo.get_all.assert_called_once()

    def test_get_supplier(self):
        self.svc.get_supplier(4)
        self.supplier_repo.get_by_id.assert_called_once_with(4)

    def test_create_supplier(self):
        data = {'name': 'Acme'}
        self.svc.create_supplier(data)
        self.supplier_repo.create.assert_called_once_with(data)

    def test_update_supplier(self):
        data = {'name': 'Acme Updated'}
        self.svc.update_supplier(4, data)
        self.supplier_repo.update.assert_called_once_with(4, data)

    @patch('apps.purchasing.models.PurchaseOrder')
    def test_delete_supplier_no_open_pos(self, mock_po):
        mock_po.Status.DRAFT = 'draft'
        mock_po.Status.PENDING_APPROVAL = 'pending_approval'
        mock_po.Status.APPROVED = 'approved'
        mock_po.Status.SENT = 'sent'
        mock_po.objects.filter.return_value.exists.return_value = False
        self.svc.delete_supplier(4)
        self.supplier_repo.soft_delete.assert_called_once_with(4)

    @patch('apps.purchasing.models.PurchaseOrder')
    def test_delete_supplier_with_open_pos_raises(self, mock_po):
        mock_po.Status.DRAFT = 'draft'
        mock_po.Status.PENDING_APPROVAL = 'pending_approval'
        mock_po.Status.APPROVED = 'approved'
        mock_po.Status.SENT = 'sent'
        mock_po.objects.filter.return_value.exists.return_value = True
        with self.assertRaises(ValidationError) as ctx:
            self.svc.delete_supplier(4)
        self.assertIn('Cannot delete supplier', str(ctx.exception))
        self.supplier_repo.soft_delete.assert_not_called()


# ---------------------------------------------------------------------------
# _parse_invoice_quantity
# ---------------------------------------------------------------------------


class ParseInvoiceQuantityTest(TestCase):
    def setUp(self):
        self.svc = InventoryService()

    def test_valid_quantity_from_quantity_received(self):
        result = self.svc._parse_invoice_quantity({'quantity_received': '5'})
        self.assertEqual(result, 5)

    def test_valid_quantity_from_quantity(self):
        result = self.svc._parse_invoice_quantity({'quantity': 10})
        self.assertEqual(result, 10)

    def test_quantity_received_takes_priority(self):
        result = self.svc._parse_invoice_quantity({'quantity_received': '3', 'quantity': '8'})
        self.assertEqual(result, 3)

    def test_zero_quantity_raises(self):
        with self.assertRaises(ValidationError):
            self.svc._parse_invoice_quantity({'quantity': '0'})

    def test_negative_quantity_raises(self):
        with self.assertRaises(ValidationError):
            self.svc._parse_invoice_quantity({'quantity': '-1'})

    def test_string_integer_quantity(self):
        result = self.svc._parse_invoice_quantity({'quantity': '7'})
        self.assertEqual(result, 7)


# ---------------------------------------------------------------------------
# _parse_invoice_price
# ---------------------------------------------------------------------------


class ParseInvoicePriceTest(TestCase):
    def setUp(self):
        self.svc = InventoryService()

    def test_none_returns_none(self):
        self.assertIsNone(self.svc._parse_invoice_price(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.svc._parse_invoice_price(''))

    def test_valid_price(self):
        result = self.svc._parse_invoice_price('12.50')
        self.assertEqual(result, Decimal('12.50'))

    def test_price_with_dollar_sign(self):
        result = self.svc._parse_invoice_price('$19.99')
        self.assertEqual(result, Decimal('19.99'))

    def test_price_with_comma(self):
        result = self.svc._parse_invoice_price('1,250.00')
        self.assertEqual(result, Decimal('1250.00'))

    def test_price_with_dollar_and_comma(self):
        result = self.svc._parse_invoice_price('$1,250.00')
        self.assertEqual(result, Decimal('1250.00'))

    def test_negative_price_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc._parse_invoice_price('-5.00')
        self.assertIn('cannot be negative', str(ctx.exception))

    def test_invalid_price_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc._parse_invoice_price('abc')
        self.assertIn('valid decimal', str(ctx.exception))

    def test_zero_price_is_valid(self):
        result = self.svc._parse_invoice_price('0')
        self.assertEqual(result, Decimal('0.00'))

    def test_quantized_to_two_decimals(self):
        result = self.svc._parse_invoice_price('9.999')
        self.assertEqual(result, Decimal('10.00'))

    def test_integer_input(self):
        result = self.svc._parse_invoice_price(25)
        self.assertEqual(result, Decimal('25.00'))


# ---------------------------------------------------------------------------
# SKUService
# ---------------------------------------------------------------------------


class SKUServiceTest(TestCase):
    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.SKURepository')
    def test_get_all_skus(self, mock_repo_cls, mock_inv):
        svc = SKUService()
        svc.repo = MagicMock()
        svc.get_all_skus()
        svc.repo.get_all.assert_called_once()

    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.SKURepository')
    def test_get_sku(self, mock_repo_cls, mock_inv):
        svc = SKUService()
        svc.repo = MagicMock()
        svc.get_sku(5)
        svc.repo.get_by_id.assert_called_once_with(5)

    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.SKURepository')
    def test_create_sku(self, mock_repo_cls, mock_inv):
        svc = SKUService()
        svc.repo = MagicMock()
        data = {'code': 'SKU-X'}
        svc.create_sku(data)
        svc.repo.create.assert_called_once_with(data)
        mock_inv.assert_called_once()

    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.SKURepository')
    def test_update_sku(self, mock_repo_cls, mock_inv):
        svc = SKUService()
        svc.repo = MagicMock()
        data = {'code': 'SKU-Y'}
        svc.update_sku(3, data)
        svc.repo.update.assert_called_once_with(3, data)
        mock_inv.assert_called_once()

    @patch('apps.inventory.services._invalidate_product_cache')
    @patch('apps.inventory.services.SKURepository')
    def test_delete_sku(self, mock_repo_cls, mock_inv):
        svc = SKUService()
        svc.repo = MagicMock()
        svc.delete_sku(3)
        svc.repo.delete.assert_called_once_with(3)
        mock_inv.assert_called_once()


# ---------------------------------------------------------------------------
# SalesRecordService
# ---------------------------------------------------------------------------


class SalesRecordServiceTest(TestCase):
    @patch('apps.inventory.services.SalesRecordRepository')
    def test_get_all_sales_records(self, mock_repo_cls):
        svc = SalesRecordService()
        svc.repo = MagicMock()
        svc.get_all_sales_records()
        svc.repo.get_all.assert_called_once()

    @patch('apps.inventory.services.SalesRecordRepository')
    def test_get_sales_record(self, mock_repo_cls):
        svc = SalesRecordService()
        svc.repo = MagicMock()
        svc.get_sales_record(8)
        svc.repo.get_by_id.assert_called_once_with(8)

    @patch('apps.inventory.services.SalesRecordRepository')
    def test_create_sales_record(self, mock_repo_cls):
        svc = SalesRecordService()
        svc.repo = MagicMock()
        data = {'sku': 1, 'quantity_sold': 10}
        svc.create_sales_record(data)
        svc.repo.create.assert_called_once_with(data)

    @patch('apps.inventory.services.SalesRecordRepository')
    def test_update_sales_record(self, mock_repo_cls):
        svc = SalesRecordService()
        svc.repo = MagicMock()
        data = {'quantity_sold': 20}
        svc.update_sales_record(8, data)
        svc.repo.update.assert_called_once_with(8, data)

    @patch('apps.inventory.services.SalesRecordRepository')
    def test_delete_sales_record(self, mock_repo_cls):
        svc = SalesRecordService()
        svc.repo = MagicMock()
        svc.delete_sales_record(8)
        svc.repo.delete.assert_called_once_with(8)
