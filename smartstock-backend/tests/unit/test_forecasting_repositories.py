import datetime

from django.test import TestCase
from django.utils import timezone

from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.forecasting.repositories import ForecastingRepository
from apps.inventory.models import Category, Product, SalesRecord, SKU


class ForecastingRepositoryTest(TestCase):
    def setUp(self):
        self.repo = ForecastingRepository()

        self.category = Category.objects.create(name='Forecast Test Cat')
        self.product = Product.objects.create(
            name='Forecast Test Product',
            category=self.category,
            is_active=True,
        )
        self.sku = SKU.objects.create(
            product=self.product,
            code='FC-SKU-001',
            attributes={'size': 'M'},
        )
        self.today = timezone.localdate()
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.tomorrow = self.today + datetime.timedelta(days=1)

    def _create_forecast(self, forecast_date=None, predicted_quantity=10.0, **overrides):
        if forecast_date is None:
            forecast_date = self.today
        defaults = {
            'sku': self.sku,
            'forecast_date': forecast_date,
            'predicted_quantity': predicted_quantity,
        }
        defaults.update(overrides)
        return ForecastResult.objects.create(**defaults)


class ForecastingRepositoryGetByIdTest(ForecastingRepositoryTest):
    def test_get_by_id_returns_correct_forecast(self):
        fc = self._create_forecast(predicted_quantity=42.0)
        result = self.repo.get_by_id(fc.id)
        self.assertEqual(result.id, fc.id)
        self.assertEqual(result.predicted_quantity, 42.0)

    def test_get_by_id_nonexistent_raises(self):
        from django.core.exceptions import ObjectDoesNotExist

        with self.assertRaises(ObjectDoesNotExist):
            self.repo.get_by_id(99999)


class ForecastingRepositoryGetAllTest(ForecastingRepositoryTest):
    def test_get_all_empty(self):
        result = self.repo.get_all()
        self.assertEqual(result.count(), 0)

    def test_get_all_returns_all(self):
        fc1 = self._create_forecast(forecast_date=self.today, predicted_quantity=1.0)
        fc2 = self._create_forecast(forecast_date=self.tomorrow, predicted_quantity=2.0)
        result = self.repo.get_all()
        self.assertEqual(result.count(), 2)
        ids = set(result.values_list('id', flat=True))
        self.assertIn(fc1.id, ids)
        self.assertIn(fc2.id, ids)


class ForecastingRepositoryGetBySkuTest(ForecastingRepositoryTest):
    def test_get_by_sku_returns_only_that_sku(self):
        other_sku = SKU.objects.create(product=self.product, code='FC-SKU-002')
        fc1 = self._create_forecast(sku=self.sku, forecast_date=self.today, predicted_quantity=5.0)
        fc2 = self._create_forecast(sku=other_sku, forecast_date=self.today, predicted_quantity=9.0)
        result = self.repo.get_by_sku(self.sku.id)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().id, fc1.id)

    def test_get_by_sku_ordered_by_forecast_date(self):
        fc_early = self._create_forecast(forecast_date=self.yesterday, predicted_quantity=1.0)
        fc_late = self._create_forecast(forecast_date=self.tomorrow, predicted_quantity=2.0)
        result = self.repo.get_by_sku(self.sku.id)
        dates = list(result.values_list('forecast_date', flat=True))
        self.assertEqual(dates, sorted(dates))

    def test_get_by_sku_no_results(self):
        result = self.repo.get_by_sku(99999)
        self.assertEqual(result.count(), 0)


class ForecastingRepositoryGetNextForProductTest(ForecastingRepositoryTest):
    def test_get_next_returns_future_forecasts(self):
        fc_past = self._create_forecast(forecast_date=self.yesterday, predicted_quantity=1.0)
        fc_future = self._create_forecast(forecast_date=self.tomorrow, predicted_quantity=2.0)
        result = list(self.repo.get_next_for_product(self.product.id))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, fc_future.id)

    def test_get_next_includes_today(self):
        fc_today = self._create_forecast(forecast_date=self.today, predicted_quantity=1.0)
        result = list(self.repo.get_next_for_product(self.product.id))
        self.assertEqual(len(result), 1)

    def test_get_next_respects_forecast_days_limit(self):
        dates = [self.today + datetime.timedelta(days=i) for i in range(10)]
        for d in dates:
            self._create_forecast(forecast_date=d, predicted_quantity=float(d.day))
        result = list(self.repo.get_next_for_product(self.product.id, forecast_days=3))
        self.assertEqual(len(result), 3)

    def test_get_next_only_checks_given_product(self):
        other_product = Product.objects.create(name='Other', category=self.category)
        other_sku = SKU.objects.create(product=other_product, code='OTHER-SKU')
        fc_other = ForecastResult.objects.create(
            sku=other_sku,
            forecast_date=self.tomorrow,
            predicted_quantity=5.0,
        )
        result = list(self.repo.get_next_for_product(self.product.id))
        self.assertEqual(len(result), 0)

    def test_get_next_returns_empty_when_no_future(self):
        self._create_forecast(forecast_date=self.yesterday, predicted_quantity=1.0)
        result = list(self.repo.get_next_for_product(self.product.id))
        self.assertEqual(len(result), 0)


class ForecastingRepositoryCreateTest(ForecastingRepositoryTest):
    def test_create_forecast(self):
        data = {
            'sku': self.sku,
            'forecast_date': self.today,
            'predicted_quantity': 55.0,
            'lower_bound': 45.0,
            'upper_bound': 65.0,
        }
        result = self.repo.create(data)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.predicted_quantity, 55.0)
        self.assertEqual(result.lower_bound, 45.0)
        self.assertEqual(result.upper_bound, 65.0)

    def test_create_persists_to_db(self):
        data = {
            'sku': self.sku,
            'forecast_date': self.today,
            'predicted_quantity': 10.0,
        }
        result = self.repo.create(data)
        self.assertTrue(ForecastResult.objects.filter(pk=result.id).exists())

    def test_create_with_model_version(self):
        data = {
            'sku': self.sku,
            'forecast_date': self.today,
            'predicted_quantity': 10.0,
            'model_version': 'prophet-1.0',
        }
        result = self.repo.create(data)
        self.assertEqual(result.model_version, 'prophet-1.0')


class ForecastingRepositoryUpdateTest(ForecastingRepositoryTest):
    def test_update_predicted_quantity(self):
        fc = self._create_forecast(predicted_quantity=10.0)
        result = self.repo.update(fc.id, {'predicted_quantity': 20.0})
        self.assertEqual(result.predicted_quantity, 20.0)

    def test_update_returns_fresh_instance(self):
        fc = self._create_forecast(predicted_quantity=10.0)
        result = self.repo.update(fc.id, {'mae': 1.5})
        self.assertEqual(result.mae, 1.5)
        fresh = ForecastResult.objects.get(pk=fc.id)
        self.assertEqual(fresh.mae, 1.5)

    def test_update_multiple_fields(self):
        fc = self._create_forecast()
        result = self.repo.update(
            fc.id,
            {
                'predicted_quantity': 99.0,
                'mape': 0.05,
                'model_version': 'v2',
            },
        )
        self.assertEqual(result.predicted_quantity, 99.0)
        self.assertEqual(result.mape, 0.05)
        self.assertEqual(result.model_version, 'v2')


class ForecastingRepositoryDeleteTest(ForecastingRepositoryTest):
    def test_delete_removes_forecast(self):
        fc = self._create_forecast()
        self.repo.delete(fc.id)
        self.assertFalse(ForecastResult.objects.filter(pk=fc.id).exists())

    def test_delete_only_removes_specified(self):
        fc1 = self._create_forecast(forecast_date=self.today)
        fc2 = self._create_forecast(forecast_date=self.tomorrow)
        self.repo.delete(fc1.id)
        self.assertFalse(ForecastResult.objects.filter(pk=fc1.id).exists())
        self.assertTrue(ForecastResult.objects.filter(pk=fc2.id).exists())


class ForecastingRepositoryGetAllSkusTest(ForecastingRepositoryTest):
    def test_get_all_skus_returns_all_skus(self):
        sku2 = SKU.objects.create(product=self.product, code='FC-SKU-002')
        result = self.repo.get_all_skus()
        codes = set(result.values_list('code', flat=True))
        self.assertIn('FC-SKU-001', codes)
        self.assertIn('FC-SKU-002', codes)

    def test_get_all_skus_includes_product(self):
        result = self.repo.get_all_skus()
        sku = result.first()
        self.assertIsNotNone(sku.product)

    def test_get_all_skus_empty(self):
        SKU.objects.all().delete()
        result = self.repo.get_all_skus()
        self.assertEqual(result.count(), 0)


class ForecastingRepositoryGetSkuTest(ForecastingRepositoryTest):
    def test_get_sku_returns_correct(self):
        result = self.repo.get_sku(self.sku.id)
        self.assertEqual(result.id, self.sku.id)
        self.assertEqual(result.code, 'FC-SKU-001')

    def test_get_sku_nonexistent_raises(self):
        from django.core.exceptions import ObjectDoesNotExist

        with self.assertRaises(ObjectDoesNotExist):
            self.repo.get_sku(99999)


class ForecastingRepositoryGetPrimarySkuForProductTest(ForecastingRepositoryTest):
    def test_returns_first_sku_for_product(self):
        new_product = Product.objects.create(name='Primary Test', category=self.category)
        sku1 = SKU.objects.create(product=new_product, code='PRI-001')
        sku2 = SKU.objects.create(product=new_product, code='PRI-002')
        result = self.repo.get_primary_sku_for_product(new_product.id)
        self.assertEqual(result.id, sku1.id)

    def test_returns_none_when_no_skus(self):
        product = Product.objects.create(name='Empty', category=self.category)
        result = self.repo.get_primary_sku_for_product(product.id)
        self.assertIsNone(result)

    def test_only_returns_skus_for_given_product(self):
        other_product = Product.objects.create(name='Other', category=self.category)
        other_sku = SKU.objects.create(product=other_product, code='OTHER')
        result = self.repo.get_primary_sku_for_product(other_product.id)
        self.assertEqual(result.id, other_sku.id)


class ForecastingRepositoryGetSkuByCodeTest(ForecastingRepositoryTest):
    def test_get_sku_by_code(self):
        result = self.repo.get_sku_by_code('FC-SKU-001')
        self.assertEqual(result.id, self.sku.id)

    def test_get_sku_by_code_nonexistent_raises(self):
        from django.core.exceptions import ObjectDoesNotExist

        with self.assertRaises(ObjectDoesNotExist):
            self.repo.get_sku_by_code('NONEXISTENT')


class ForecastingRepositoryUpsertOpenReorderFlagTest(ForecastingRepositoryTest):
    def _flag_data(self, **overrides):
        data = {
            'quantity_available': 5,
            'total_predicted_demand': 20.0,
            'safety_stock': 10,
            'reorder_required': True,
            'reasoning': 'Low stock',
        }
        data.update(overrides)
        return data

    def test_creates_new_open_flag(self):
        result = self.repo.upsert_open_reorder_flag(self.sku.id, self._flag_data())
        self.assertIsNotNone(result.id)
        self.assertEqual(result.status, ReorderFlag.Status.OPEN)
        self.assertEqual(result.sku_id, self.sku.id)

    def test_updates_existing_open_flag(self):
        flag = ReorderFlag.objects.create(
            sku=self.sku,
            quantity_available=5,
            total_predicted_demand=20.0,
            safety_stock=10,
            reorder_required=True,
            reasoning='old reasoning',
            status=ReorderFlag.Status.OPEN,
        )
        result = self.repo.upsert_open_reorder_flag(
            self.sku.id,
            self._flag_data(reasoning='updated reasoning'),
        )
        result.refresh_from_db()
        self.assertEqual(result.reasoning, 'updated reasoning')
        self.assertEqual(result.id, flag.id)

    def test_does_not_update_consumed_flag(self):
        old_flag = ReorderFlag.objects.create(
            sku=self.sku,
            quantity_available=5,
            total_predicted_demand=20.0,
            safety_stock=10,
            reorder_required=True,
            reasoning='consumed flag',
            status=ReorderFlag.Status.CONSUMED,
        )
        result = self.repo.upsert_open_reorder_flag(
            self.sku.id,
            self._flag_data(reasoning='new open flag'),
        )
        self.assertNotEqual(result.id, old_flag.id)
        self.assertEqual(result.status, ReorderFlag.Status.OPEN)
        old_flag.refresh_from_db()
        self.assertEqual(old_flag.reasoning, 'consumed flag')

    def test_sets_has_open_po(self):
        result = self.repo.upsert_open_reorder_flag(
            self.sku.id,
            self._flag_data(has_open_po=True, open_po_id=42),
        )
        self.assertTrue(result.has_open_po)
        self.assertEqual(result.open_po_id, 42)


class ForecastingRepositoryGetSalesForSkuTest(ForecastingRepositoryTest):
    def test_returns_sales_for_sku(self):
        sr1 = SalesRecord.objects.create(sku=self.sku, date=self.yesterday, quantity_sold=5)
        sr2 = SalesRecord.objects.create(sku=self.sku, date=self.today, quantity_sold=10)
        result = self.repo.get_sales_for_sku(self.sku.id)
        self.assertEqual(result.count(), 2)

    def test_sales_ordered_by_date(self):
        sr1 = SalesRecord.objects.create(sku=self.sku, date=self.today, quantity_sold=10)
        sr2 = SalesRecord.objects.create(sku=self.sku, date=self.yesterday, quantity_sold=5)
        result = self.repo.get_sales_for_sku(self.sku.id)
        dates = list(result.values_list('date', flat=True))
        self.assertEqual(dates, sorted(dates))

    def test_only_returns_sales_for_given_sku(self):
        other_sku = SKU.objects.create(product=self.product, code='OTHER-SALES')
        SalesRecord.objects.create(sku=self.sku, date=self.today, quantity_sold=10)
        SalesRecord.objects.create(sku=other_sku, date=self.today, quantity_sold=20)
        result = self.repo.get_sales_for_sku(self.sku.id)
        self.assertEqual(result.count(), 1)

    def test_no_sales_returns_empty(self):
        result = self.repo.get_sales_for_sku(99999)
        self.assertEqual(result.count(), 0)


class ForecastingRepositoryGetSalesForAllSkusTest(ForecastingRepositoryTest):
    def test_returns_dict_of_sku_code_to_queryset(self):
        SalesRecord.objects.create(sku=self.sku, date=self.today, quantity_sold=10)
        result = self.repo.get_sales_for_all_skus()
        self.assertIsInstance(result, dict)
        self.assertIn('FC-SKU-001', result)
        self.assertEqual(result['FC-SKU-001'].count(), 1)

    def test_skus_without_sales_excluded(self):
        SKU.objects.create(product=self.product, code='NO-SALES')
        result = self.repo.get_sales_for_all_skus()
        self.assertNotIn('NO-SALES', result)

    def test_inactive_products_excluded(self):
        inactive_product = Product.objects.create(
            name='Inactive', category=self.category, is_active=False
        )
        inactive_sku = SKU.objects.create(product=inactive_product, code='INACTIVE-SKU')
        SalesRecord.objects.create(sku=inactive_sku, date=self.today, quantity_sold=5)
        result = self.repo.get_sales_for_all_skus()
        self.assertNotIn('INACTIVE-SKU', result)

    def test_empty_when_no_sales(self):
        result = self.repo.get_sales_for_all_skus()
        self.assertEqual(result, {})


class ForecastingRepositoryUpsertTest(ForecastingRepositoryTest):
    def test_creates_new_forecast(self):
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=15.0,
            lower_bound=10.0,
            upper_bound=20.0,
            mae=1.2,
            mape=0.08,
            model_version='prophet-v1',
        )
        fc = ForecastResult.objects.get(sku=self.sku, forecast_date=self.today)
        self.assertEqual(fc.predicted_quantity, 15.0)
        self.assertEqual(fc.lower_bound, 10.0)
        self.assertEqual(fc.upper_bound, 20.0)
        self.assertEqual(fc.mae, 1.2)
        self.assertEqual(fc.mape, 0.08)
        self.assertEqual(fc.model_version, 'prophet-v1')

    def test_updates_existing_forecast(self):
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=15.0,
        )
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=25.0,
            model_version='prophet-v2',
        )
        fc = ForecastResult.objects.get(sku=self.sku, forecast_date=self.today)
        self.assertEqual(fc.predicted_quantity, 25.0)
        self.assertEqual(fc.model_version, 'prophet-v2')

    def test_does_not_create_second_record(self):
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=15.0,
        )
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=25.0,
        )
        self.assertEqual(ForecastResult.objects.count(), 1)

    def test_upsert_different_dates_creates_separate(self):
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=10.0,
        )
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.tomorrow),
            predicted_quantity=20.0,
        )
        self.assertEqual(ForecastResult.objects.count(), 2)

    def test_upsert_optional_fields_default_none(self):
        self.repo.upsert(
            sku_id=self.sku.id,
            forecast_date=str(self.today),
            predicted_quantity=10.0,
        )
        fc = ForecastResult.objects.get(sku=self.sku, forecast_date=self.today)
        self.assertIsNone(fc.lower_bound)
        self.assertIsNone(fc.upper_bound)
        self.assertIsNone(fc.mae)
        self.assertIsNone(fc.mape)
        self.assertEqual(fc.model_version, '')


class ForecastingRepositoryForecastResultOrderingTest(ForecastingRepositoryTest):
    def test_ordered_by_created_at_desc(self):
        fc1 = self._create_forecast(forecast_date=self.yesterday, predicted_quantity=1.0)
        fc2 = self._create_forecast(forecast_date=self.tomorrow, predicted_quantity=2.0)
        result = list(ForecastResult.objects.all())
        self.assertEqual(result[0].id, fc2.id)
        self.assertEqual(result[1].id, fc1.id)


class ForecastingRepositoryReorderFlagOrderingTest(ForecastingRepositoryTest):
    def test_ordered_by_created_at_desc(self):
        flag1 = ReorderFlag.objects.create(
            sku=self.sku,
            quantity_available=1,
            total_predicted_demand=10.0,
            safety_stock=5,
            reorder_required=True,
            reasoning='first',
        )
        flag2 = ReorderFlag.objects.create(
            sku=self.sku,
            quantity_available=2,
            total_predicted_demand=20.0,
            safety_stock=5,
            reorder_required=True,
            reasoning='second',
        )
        result = list(ReorderFlag.objects.all())
        self.assertEqual(result[0].id, flag2.id)
        self.assertEqual(result[1].id, flag1.id)
