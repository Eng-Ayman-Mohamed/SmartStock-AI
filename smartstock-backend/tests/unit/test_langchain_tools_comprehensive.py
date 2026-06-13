from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.agents.base_agent import BaseTool
from ai.agents.tools.confirmation_listener import ConfirmationListenerTool
from ai.agents.tools.db_read import DBReadTool
from ai.agents.tools.db_update import DBUpdateTool
from ai.agents.tools.db_write import DBWriteTool
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.forecast_read import ForecastReadTool
from ai.agents.tools.po_draft import PODraftTool
from ai.agents.tools.po_status_check import POStatusCheckTool
from ai.agents.tools.stock_level_read import StockLevelReadTool


class BaseToolABCContractTest(TestCase):
    def test_basetool_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseTool()

    def test_subclass_must_implement_run(self):
        class IncompleteTool(BaseTool):
            name = 'incomplete'
            description = 'missing run'

        with self.assertRaises(TypeError):
            IncompleteTool()

    def test_subclass_with_run_works(self):
        class CompleteTool(BaseTool):
            name = 'complete'
            description = 'has run'

            def run(self, input):
                return {'ok': True}

        tool = CompleteTool()
        self.assertEqual(tool.name, 'complete')
        self.assertEqual(tool.description, 'has run')
        result = tool.run({})
        self.assertTrue(result['ok'])

    def test_all_tools_have_name_and_description(self):
        tools = [
            DBReadTool,
            DBWriteTool,
            DBUpdateTool,
            EmailSendTool,
            ForecastReadTool,
            StockLevelReadTool,
            PODraftTool,
            POStatusCheckTool,
            ConfirmationListenerTool,
        ]
        for tool_cls in tools:
            self.assertTrue(hasattr(tool_cls, 'name'), f'{tool_cls.__name__} missing name')
            self.assertTrue(
                hasattr(tool_cls, 'description'), f'{tool_cls.__name__} missing description'
            )
            self.assertIsInstance(tool_cls.name, str)
            self.assertIsInstance(tool_cls.description, str)
            self.assertTrue(len(tool_cls.name) > 0)
            self.assertTrue(len(tool_cls.description) > 0)

    def test_all_tools_are_basetool_subclasses(self):
        tools = [
            DBReadTool,
            DBWriteTool,
            DBUpdateTool,
            EmailSendTool,
            ForecastReadTool,
            StockLevelReadTool,
            PODraftTool,
            POStatusCheckTool,
            ConfirmationListenerTool,
        ]
        for tool_cls in tools:
            self.assertTrue(
                issubclass(tool_cls, BaseTool), f'{tool_cls.__name__} not subclass of BaseTool'
            )


class DBReadToolTest(TestCase):
    def test_returns_empty_data(self):
        tool = DBReadTool()
        result = tool.run({'query': 'anything'})
        self.assertEqual(result, {'data': []})

    def test_empty_input(self):
        tool = DBReadTool()
        result = tool.run({})
        self.assertEqual(result, {'data': []})

    def test_none_input(self):
        tool = DBReadTool()
        result = tool.run(None)
        self.assertEqual(result, {'data': []})

    def test_output_is_dict(self):
        tool = DBReadTool()
        result = tool.run({'key': 'value'})
        self.assertIsInstance(result, dict)

    def test_has_data_key(self):
        tool = DBReadTool()
        result = tool.run({})
        self.assertIn('data', result)

    def test_data_is_list(self):
        tool = DBReadTool()
        result = tool.run({})
        self.assertIsInstance(result['data'], list)


class DBWriteToolTest(TestCase):
    def test_returns_written_status(self):
        tool = DBWriteTool()
        result = tool.run({'table': 'products', 'data': {}})
        self.assertEqual(result, {'status': 'written'})

    def test_empty_input(self):
        tool = DBWriteTool()
        result = tool.run({})
        self.assertEqual(result, {'status': 'written'})

    def test_output_keys(self):
        tool = DBWriteTool()
        result = tool.run({})
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'written')


class DBUpdateToolTest(TestCase):
    def test_returns_updated_status(self):
        mock_service = MagicMock()
        mock_service.transition_po_status.return_value = MagicMock(id=1, status='approved')
        tool = DBUpdateTool(service=mock_service)
        result = tool.run({'po_id': '1', 'status': 'approved'})
        self.assertEqual(result, {'po_id': 1, 'status': 'approved'})

    def test_empty_input(self):
        mock_service = MagicMock()
        tool = DBUpdateTool(service=mock_service)
        with self.assertRaises(KeyError):
            tool.run({})


class StockLevelReadToolTest(TestCase):
    def test_calls_service_with_correct_product_id(self):
        captured = {}

        def fake_get_decision_stock_data(product_id):
            captured['product_id'] = product_id
            return {'product_id': product_id, 'sku_code': 'SKU-001', 'quantity_available': 42}

        tool = StockLevelReadTool(
            service=SimpleNamespace(get_decision_stock_data=fake_get_decision_stock_data)
        )
        result = tool.run({'product_id': '5'})
        self.assertEqual(captured['product_id'], 5)
        self.assertEqual(result['sku_code'], 'SKU-001')

    def test_output_schema(self):
        def fake_get_decision_stock_data(product_id):
            return {
                'product_id': product_id,
                'sku_code': 'SKU-001',
                'quantity_available': 42,
                'reorder_point': 10,
                'lead_time_days': 7,
                'safety_stock': 5,
            }

        tool = StockLevelReadTool(
            service=SimpleNamespace(get_decision_stock_data=fake_get_decision_stock_data)
        )
        result = tool.run({'product_id': '1'})
        self.assertIn('product_id', result)
        self.assertIn('sku_code', result)
        self.assertIn('quantity_available', result)

    def test_invalid_product_id(self):
        def fake_get_decision_stock_data(product_id):
            raise ValueError(f'Invalid product_id: {product_id}')

        tool = StockLevelReadTool(
            service=SimpleNamespace(get_decision_stock_data=fake_get_decision_stock_data)
        )
        with self.assertRaises(ValueError):
            tool.run({'product_id': 'abc'})

    def test_string_product_id_converted(self):
        captured = {}

        def fake_get_decision_stock_data(product_id):
            captured['product_id'] = product_id
            return {'product_id': product_id}

        tool = StockLevelReadTool(
            service=SimpleNamespace(get_decision_stock_data=fake_get_decision_stock_data)
        )
        tool.run({'product_id': '42'})
        self.assertEqual(captured['product_id'], 42)

    def test_tool_name(self):
        tool = StockLevelReadTool()
        self.assertEqual(tool.name, 'stock_level_read_tool')


class ForecastReadToolTest(TestCase):
    def test_calls_service_with_default_days(self):
        captured = {}

        def fake_get_decision_forecast_data(product_id, forecast_days):
            captured['product_id'] = product_id
            captured['forecast_days'] = forecast_days
            return {
                'product_id': product_id,
                'forecast_days': forecast_days,
                'total_predicted_demand': 50.0,
            }

        tool = ForecastReadTool(
            service=SimpleNamespace(get_decision_forecast_data=fake_get_decision_forecast_data)
        )
        tool.run({'product_id': '3'})
        self.assertEqual(captured['product_id'], 3)
        self.assertEqual(captured['forecast_days'], 7)

    def test_custom_forecast_days(self):
        captured = {}

        def fake_get_decision_forecast_data(product_id, forecast_days):
            captured['forecast_days'] = forecast_days
            return {'forecast_days': forecast_days}

        tool = ForecastReadTool(
            service=SimpleNamespace(get_decision_forecast_data=fake_get_decision_forecast_data)
        )
        tool.run({'product_id': '1', 'forecast_days': '14'})
        self.assertEqual(captured['forecast_days'], 14)

    def test_output_schema(self):
        def fake_get_decision_forecast_data(product_id, forecast_days):
            return {
                'sku_code': 'SKU-001',
                'forecast_days': forecast_days,
                'total_predicted_demand': 100.0,
            }

        tool = ForecastReadTool(
            service=SimpleNamespace(get_decision_forecast_data=fake_get_decision_forecast_data)
        )
        result = tool.run({'product_id': '1'})
        self.assertIn('sku_code', result)
        self.assertIn('forecast_days', result)
        self.assertIn('total_predicted_demand', result)

    def test_tool_name(self):
        tool = ForecastReadTool()
        self.assertEqual(tool.name, 'forecast_read_tool')


class POStatusCheckToolTest(TestCase):
    def test_no_open_po(self):
        def fake_get_open_po_status(product_id):
            return {'has_open_po': False, 'open_po_id': None}

        tool = POStatusCheckTool(
            service=SimpleNamespace(get_open_po_status=fake_get_open_po_status)
        )
        result = tool.run({'product_id': '1'})
        self.assertFalse(result['has_open_po'])
        self.assertIsNone(result['open_po_id'])

    def test_has_open_po(self):
        def fake_get_open_po_status(product_id):
            return {'has_open_po': True, 'open_po_id': 42}

        tool = POStatusCheckTool(
            service=SimpleNamespace(get_open_po_status=fake_get_open_po_status)
        )
        result = tool.run({'product_id': '1'})
        self.assertTrue(result['has_open_po'])
        self.assertEqual(result['open_po_id'], 42)

    def test_tool_name(self):
        tool = POStatusCheckTool()
        self.assertEqual(tool.name, 'po_status_check_tool')


class PODraftToolTest(TestCase):
    def test_creates_draft_po(self):
        mock_po = SimpleNamespace(id=10, status='draft', sku_id=5, supplier_id=3, quantity=100)
        mock_repo = SimpleNamespace(create=lambda data: mock_po)
        tool = PODraftTool(service=SimpleNamespace(repo=mock_repo))
        result = tool.run(
            {
                'sku_id': '5',
                'quantity': '100',
                'supplier_id': '3',
                'total_cost': '500.00',
            }
        )
        self.assertEqual(result['po_id'], 10)
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['sku_id'], 5)
        self.assertEqual(result['quantity'], 100)

    def test_includes_user_id(self):
        captured = {}

        def fake_create(data):
            captured.update(data)
            return SimpleNamespace(id=20, status='draft', sku_id=1, supplier_id=1, quantity=10)

        tool = PODraftTool(service=SimpleNamespace(repo=SimpleNamespace(create=fake_create)))
        tool.run(
            {
                'sku_id': '1',
                'quantity': '10',
                'supplier_id': '1',
                'user_id': '99',
                'agent_reasoning': 'low stock',
            }
        )
        self.assertEqual(captured['requested_by_id'], 99)
        self.assertEqual(captured['agent_reasoning'], 'low stock')

    def test_failure_returns_error(self):
        def fake_create(data):
            raise ValueError('DB error')

        tool = PODraftTool(service=SimpleNamespace(repo=SimpleNamespace(create=fake_create)))
        result = tool.run({'sku_id': '1', 'quantity': '10', 'supplier_id': '1'})
        self.assertIsNone(result['po_id'])
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)

    def test_tool_name(self):
        tool = PODraftTool()
        self.assertEqual(tool.name, 'po_draft_tool')


class EmailSendToolTest(TestCase):
    @patch('ai.agents.tools.email_send.send_email_with_retry')
    def test_successful_send(self, mock_task):
        mock_result = MagicMock(id='task-123')
        mock_task.delay.return_value = mock_result
        mock_po = SimpleNamespace(
            id=1,
            status='approved',
            sku=SimpleNamespace(code='SKU-001', product=SimpleNamespace(name='Widget')),
            quantity=100,
            total_cost=500.00,
            requested_by='admin',
            supplier=SimpleNamespace(name='Acme', contact_email='acme@example.com'),
        )
        mock_repo = SimpleNamespace(get_by_id=lambda po_id: mock_po)
        mock_purchasing = SimpleNamespace(repo=mock_repo)
        tool = EmailSendTool(purchasing_service=mock_purchasing)
        result = tool.run({'po_id': '1'})
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['po_id'], 1)
        self.assertIn('message_id', result)

    def test_po_not_approved_fails(self):
        mock_po = SimpleNamespace(id=1, status='draft')
        mock_repo = SimpleNamespace(get_by_id=lambda po_id: mock_po)
        tool = EmailSendTool(
            purchasing_service=SimpleNamespace(repo=mock_repo),
        )
        result = tool.run({'po_id': '1'})
        self.assertEqual(result['status'], 'failed')
        self.assertIn('not in approved/sent', result['error'])

    def test_missing_po_id_fails(self):
        tool = EmailSendTool(
            purchasing_service=SimpleNamespace(repo=SimpleNamespace(get_by_id=lambda x: None)),
        )
        result = tool.run({})
        self.assertEqual(result['status'], 'failed')

    def test_invalid_po_id_string(self):
        tool = EmailSendTool(
            purchasing_service=SimpleNamespace(repo=SimpleNamespace(get_by_id=lambda x: None)),
        )
        result = tool.run({'po_id': 'not_a_number'})
        self.assertEqual(result['status'], 'failed')

    def test_tool_name(self):
        tool = EmailSendTool()
        self.assertEqual(tool.name, 'email_send_tool')

    def test_build_email_body(self):
        tool = EmailSendTool()
        body = tool._build_email_body(
            po_id=1,
            sku_code='SKU-001',
            product_name='Widget',
            quantity=100,
            total_cost=500.00,
            requested_by='admin',
            supplier_name='Acme',
        )
        self.assertIn('Purchase Order PO-1', body)
        self.assertIn('SKU-001', body)
        self.assertIn('Widget', body)
        self.assertIn('Acme', body)


class ConfirmationListenerToolTest(TestCase):
    def test_confirmed(self):
        mock_po = SimpleNamespace(status='confirmed')
        mock_repo = SimpleNamespace(get_by_id=lambda po_id: mock_po)
        tool = ConfirmationListenerTool(purchasing_service=SimpleNamespace(repo=mock_repo))
        result = tool.run({'po_id': '1'})
        self.assertTrue(result['confirmed'])
        self.assertEqual(result['status'], 'confirmed')

    def test_pending(self):
        mock_po = SimpleNamespace(status='waiting_confirmation')
        mock_repo = SimpleNamespace(get_by_id=lambda po_id: mock_po)
        tool = ConfirmationListenerTool(purchasing_service=SimpleNamespace(repo=mock_repo))
        result = tool.run({'po_id': '1'})
        self.assertFalse(result['confirmed'])
        self.assertEqual(result['status'], 'waiting_confirmation')

    def test_terminal_rejected(self):
        for status in ['rejected', 'cancelled', 'failed', 'timeout']:
            mock_po = SimpleNamespace(status=status)
            mock_repo = SimpleNamespace(get_by_id=lambda po_id, s=status: mock_po)
            tool = ConfirmationListenerTool(purchasing_service=SimpleNamespace(repo=mock_repo))
            result = tool.run({'po_id': '1'})
            self.assertFalse(result['confirmed'])
            self.assertTrue(result['terminal'])

    def test_exception_handling(self):
        def bad_get_by_id(po_id):
            raise Exception('DB connection lost')

        tool = ConfirmationListenerTool(
            purchasing_service=SimpleNamespace(repo=SimpleNamespace(get_by_id=bad_get_by_id))
        )
        result = tool.run({'po_id': '1'})
        self.assertFalse(result['confirmed'])
        self.assertIn('error', result)

    def test_tool_name(self):
        tool = ConfirmationListenerTool()
        self.assertEqual(tool.name, 'confirmation_listener_tool')

    def test_invalid_po_id(self):
        tool = ConfirmationListenerTool(
            purchasing_service=SimpleNamespace(repo=SimpleNamespace(get_by_id=lambda x: None))
        )
        result = tool.run({'po_id': 'not_a_number'})
        self.assertFalse(result['confirmed'])
        self.assertIn('error', result)
