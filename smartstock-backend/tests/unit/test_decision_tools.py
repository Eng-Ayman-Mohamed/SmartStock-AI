from types import SimpleNamespace

from ai.agents.tools.forecast_read import ForecastReadTool
from ai.agents.tools.po_status_check import POStatusCheckTool
from ai.agents.tools.stock_level_read import StockLevelReadTool
from apps.forecasting.services import ForecastingService
from apps.inventory.services import InventoryService
from apps.purchasing.services import PurchasingService


class FakeStock:
    def __init__(self):
        supplier = SimpleNamespace(default_lead_time_days=9)
        product = SimpleNamespace(id=1, reorder_point=20, safety_stock=8, supplier=supplier)
        self.sku = SimpleNamespace(code='SKU-001', product=product)
        self.reorder_point = 15

    @property
    def quantity_available(self):
        return 42


class FakeStockRepository:
    def get_by_product_id(self, product_id):
        assert product_id == 1
        return FakeStock()


class FakeForecastRepository:
    def get_next_for_product(self, product_id, forecast_days):
        assert product_id == 1
        assert forecast_days == 7
        sku = SimpleNamespace(code='SKU-001')
        return [
            SimpleNamespace(sku=sku, predicted_quantity=10.5),
            SimpleNamespace(sku=sku, predicted_quantity=11.25),
            SimpleNamespace(sku=sku, predicted_quantity=12),
        ]

    def get_primary_sku_for_product(self, product_id):
        return SimpleNamespace(code='SKU-001')


class FakePurchasingRepository:
    def __init__(self, open_po=None):
        self.open_po = open_po

    def get_open_for_product(self, product_id):
        assert product_id == 1
        return self.open_po


def test_inventory_service_returns_decision_stock_payload_from_repository():
    service = InventoryService(repo=object(), stock_repo=FakeStockRepository(), cat_repo=object())

    result = service.get_decision_stock_data(1)

    assert result == {
        'product_id': 1,
        'sku_code': 'SKU-001',
        'quantity_available': 42,
        'reorder_point': 15,
        'lead_time_days': 9,
        'safety_stock': 8,
    }


def test_forecasting_service_sums_next_forecast_rows_from_repository():
    service = ForecastingService(repo=FakeForecastRepository(), engine=object())

    result = service.get_decision_forecast_data(1, 7)

    assert result == {
        'sku_code': 'SKU-001',
        'forecast_days': 7,
        'total_predicted_demand': 33.75,
    }


def test_purchasing_service_reports_no_open_po():
    service = PurchasingService(repo=FakePurchasingRepository())

    result = service.get_open_po_status(1)

    assert result == {'has_open_po': False, 'open_po_id': None}


def test_purchasing_service_reports_existing_open_po():
    service = PurchasingService(repo=FakePurchasingRepository(open_po=SimpleNamespace(id=123)))

    result = service.get_open_po_status(1)

    assert result == {'has_open_po': True, 'open_po_id': 123}


def test_stock_level_read_tool_calls_service():
    service = SimpleNamespace(get_decision_stock_data=lambda product_id: {'product_id': product_id})

    result = StockLevelReadTool(service=service).run({'product_id': '1'})

    assert result == {'product_id': 1}


def test_forecast_read_tool_calls_service_with_default_window():
    service = SimpleNamespace(
        get_decision_forecast_data=lambda product_id, forecast_days: {
            'product_id': product_id,
            'forecast_days': forecast_days,
        }
    )

    result = ForecastReadTool(service=service).run({'product_id': '1'})

    assert result == {'product_id': 1, 'forecast_days': 7}


def test_po_status_check_tool_calls_service():
    service = SimpleNamespace(get_open_po_status=lambda product_id: {'checked_product_id': product_id})

    result = POStatusCheckTool(service=service).run({'product_id': '1'})

    assert result == {'checked_product_id': 1}
