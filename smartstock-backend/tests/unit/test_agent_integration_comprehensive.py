from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from ai.agents.decision_agent import DecisionAgent, DecisionReasoner
from ai.agents.forecasting_agent import ForecastingAgent
from ai.agents.purchasing_agent import PurchasingAgent
from apps.purchasing.workflow_models import PurchaseOrderWorkflow


class FakeStockTool:
    name = 'stock_level_read_tool'

    def __init__(self, quantity_available=50, reorder_point=20, lead_time_days=7, safety_stock=10):
        self.quantity_available = quantity_available
        self.reorder_point = reorder_point
        self.lead_time_days = lead_time_days
        self.safety_stock = safety_stock

    def run(self, input):
        return {
            'product_id': int(input['product_id']),
            'sku_code': 'SKU-001',
            'quantity_available': self.quantity_available,
            'reorder_point': self.reorder_point,
            'lead_time_days': self.lead_time_days,
            'safety_stock': self.safety_stock,
        }


class FakeForecastTool:
    name = 'forecast_read_tool'

    def __init__(self, total_predicted_demand=30.0):
        self.total_predicted_demand = total_predicted_demand
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        return {
            'sku_code': 'SKU-001',
            'forecast_days': int(input.get('forecast_days', 7)),
            'total_predicted_demand': self.total_predicted_demand,
        }


class FakePOStatusTool:
    name = 'po_status_check_tool'

    def __init__(self, has_open_po=False, open_po_id=None):
        self.has_open_po = has_open_po
        self.open_po_id = open_po_id

    def run(self, input):
        return {'has_open_po': self.has_open_po, 'open_po_id': self.open_po_id}


class FakeForecastingService:
    def __init__(self):
        self.persisted = []

    def persist_reorder_flag(self, decision):
        self.persisted.append(decision)
        return SimpleNamespace(id=77)

    def get_decision_forecast_data(self, product_id, forecast_days=7):
        return {
            'sku_code': 'SKU-001',
            'forecast_days': forecast_days,
            'total_predicted_demand': 50.0,
        }


class FakeReasoner:
    def generate(self, payload):
        return (
            f'Stock {payload["quantity_available"]} vs demand {payload["total_predicted_demand"]}.'
        )


class FakePODraftTool:
    def __init__(self):
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        if input.get('action') == 'trace':
            return {'status': 'traced'}
        return {'po_id': 100, 'status': 'draft', 'sku_id': 1, 'supplier_id': 1, 'quantity': 10}


class FakeEmailSendTool:
    def __init__(self, succeed=True):
        self.succeed = succeed

    def run(self, input):
        if self.succeed:
            return {'status': 'sent', 'po_id': input['po_id'], 'message_id': 'msg-123'}
        return {'status': 'failed', 'error': 'SMTP error'}


class FakeConfirmationTool:
    def __init__(self, confirm_after=0):
        self.confirm_after = confirm_after
        self.call_count = 0

    def run(self, input):
        self.call_count += 1
        if self.call_count > self.confirm_after:
            return {'confirmed': True, 'po_id': input['po_id']}
        return {'confirmed': False, 'po_id': input['po_id'], 'status': 'waiting_confirmation'}


class FakePurchasingService:
    def __init__(self):
        self.approved = []
        self.rejected = []
        self.email_sent = []
        self.waiting = []
        self.confirmed = []
        self.failed = []
        self.timeout = []

    def approve_po(self, po_id, user):
        self.approved.append(po_id)

    def reject_po(self, po_id, user):
        self.rejected.append(po_id)

    def mark_email_sent(self, po_id, message_id=None):
        self.email_sent.append(po_id)

    def mark_waiting_confirmation(self, po_id):
        self.waiting.append(po_id)

    def mark_confirmed(self, po_id):
        self.confirmed.append(po_id)

    def mark_failed(self, po_id, error=''):
        self.failed.append(po_id)

    def mark_timeout(self, po_id):
        self.timeout.append(po_id)

    def draft_po(self, sku_id, quantity, supplier_id, user):
        return SimpleNamespace(id=100, status='draft')


class FakeWorkflowService:
    def __init__(self):
        self.workflow_id_counter = 1
        self.statuses = []
        self.confirmed_workflows = []
        self.poll_increments = []

    def create_workflow(self, po_id):
        wf = SimpleNamespace(id=self.workflow_id_counter, purchase_order_id=po_id, status='draft')
        self.workflow_id_counter += 1
        return wf

    def update_status(self, workflow_id, status, message_id=None, error_message=None):
        self.statuses.append((workflow_id, status))

    def increment_polling_attempt(self, workflow_id):
        self.poll_increments.append(workflow_id)

    def mark_confirmed(self, workflow_id):
        self.confirmed_workflows.append(workflow_id)


class DecisionAgentComprehensiveTest(TestCase):
    def _build_agent(self, quantity_available=50, total_predicted_demand=30.0, has_open_po=False):
        service = FakeForecastingService()
        forecast_tool = FakeForecastTool(total_predicted_demand)
        agent = DecisionAgent(
            stock_tool=FakeStockTool(quantity_available=quantity_available),
            forecast_tool=forecast_tool,
            po_status_tool=FakePOStatusTool(has_open_po=has_open_po),
            forecasting_service=service,
            reasoner=FakeReasoner(),
        )
        return agent, service, forecast_tool

    def test_agent_initialization(self):
        agent = DecisionAgent()
        self.assertIsNotNone(agent.stock_tool)
        self.assertIsNotNone(agent.forecast_tool)
        self.assertIsNotNone(agent.po_status_tool)
        self.assertIsNotNone(agent.forecasting_service)
        self.assertIsNotNone(agent.reasoner)

    def test_run_single_product(self):
        agent, service, _ = self._build_agent(quantity_available=45, total_predicted_demand=62)
        result = agent.run({'product_id': 1})
        self.assertIn('results', result)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['agent'], 'decision_agent')

    def test_run_multiple_products(self):
        agent, _, _ = self._build_agent(quantity_available=45, total_predicted_demand=62)
        result = agent.run({'product_ids': [1, 2, 3]})
        self.assertEqual(len(result['results']), 3)

    def test_run_products_from_context(self):
        agent, _, _ = self._build_agent(quantity_available=45, total_predicted_demand=62)
        result = agent.run({'products': [{'product_id': 1}, {'product_id': 2}]})
        self.assertEqual(len(result['results']), 2)

    def test_reorder_required_when_low_stock(self):
        agent, service, _ = self._build_agent(quantity_available=5, total_predicted_demand=62)
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        self.assertTrue(decision['reorder_required'])
        self.assertEqual(result['flags_created'], 1)

    def test_no_reorder_when_sufficient_stock(self):
        agent, service, _ = self._build_agent(quantity_available=200, total_predicted_demand=30)
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        self.assertFalse(decision['reorder_required'])
        self.assertEqual(result['flags_created'], 0)
        self.assertEqual(service.persisted, [])

    def test_no_reorder_when_open_po(self):
        agent, service, _ = self._build_agent(
            quantity_available=5, total_predicted_demand=62, has_open_po=True
        )
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        self.assertFalse(decision['reorder_required'])
        self.assertTrue(decision['has_open_po'])

    def test_tool_tracing(self):
        agent, _, _ = self._build_agent()
        trace_spans = []
        agent.evaluate_product(1, trace_spans=trace_spans)
        self.assertGreater(len(trace_spans), 0)
        span_names = [s['name'] for s in trace_spans]
        self.assertIn('stock_level_read_tool', span_names)
        self.assertIn('forecast_read_tool', span_names)

    def test_empty_context_no_products(self):
        agent, _, _ = self._build_agent()
        result = agent.run({})
        self.assertEqual(result['results'], [])
        self.assertEqual(result['flags_created'], 0)

    def test_decision_result_keys(self):
        agent, _, _ = self._build_agent(quantity_available=5, total_predicted_demand=62)
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        expected_keys = [
            'product_id',
            'sku_code',
            'quantity_available',
            'reorder_point',
            'lead_time_days',
            'total_predicted_demand',
            'safety_stock',
            'has_open_po',
            'formula_requires_reorder',
            'reorder_required',
            'reasoning',
            'steps',
        ]
        for key in expected_keys:
            self.assertIn(key, decision)

    def test_reasoning_contains_numbers(self):
        agent, _, _ = self._build_agent(quantity_available=5, total_predicted_demand=62)
        result = agent.run({'product_id': 1})
        reasoning = result['results'][0]['reasoning']
        self.assertIn('5', reasoning)
        self.assertIn('62', reasoning)


class DecisionReasonerTest(TestCase):
    def test_generate_returns_string(self):
        reasoner = DecisionReasoner()
        payload = {
            'quantity_available': 10,
            'total_predicted_demand': 50,
            'lead_time_days': 7,
            'safety_stock': 5,
        }
        result = reasoner.generate(payload)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_generate_fallback_on_error(self):
        reasoner = DecisionReasoner(llm=None)
        payload = {
            'quantity_available': 10,
            'total_predicted_demand': 50,
            'lead_time_days': 7,
            'safety_stock': 5,
        }
        with patch('ai.llm.chain.get_llm', side_effect=Exception('LLM unavailable')):
            result = reasoner.generate(payload)
            self.assertIn('10', result)
            self.assertIn('50', result)

    def test_generate_with_custom_llm(self):
        mock_llm = SimpleNamespace()
        mock_chain = SimpleNamespace(invoke=lambda payload, config=None: 'Custom reasoning')
        with patch('ai.agents.decision_agent.ChatPromptTemplate') as mock_template:
            mock_template.from_messages.return_value.__or__ = lambda self, other: mock_chain
            reasoner = DecisionReasoner(llm=mock_llm)
            payload = {
                'quantity_available': 10,
                'total_predicted_demand': 50,
                'lead_time_days': 7,
                'safety_stock': 5,
            }
            try:
                result = reasoner.generate(payload)
            except Exception:
                result = reasoner.generate(payload)
            self.assertIsInstance(result, str)


class ForecastingAgentTest(TestCase):
    def test_initialization(self):
        agent = ForecastingAgent()
        self.assertIsNotNone(agent)

    def test_run_returns_not_implemented(self):
        agent = ForecastingAgent()
        result = agent.run()
        self.assertEqual(result['agent'], 'forecasting_agent')
        self.assertEqual(result['status'], 'not_implemented')

    def test_run_with_context(self):
        agent = ForecastingAgent()
        result = agent.run({'sku_id': 1})
        self.assertEqual(result['agent'], 'forecasting_agent')

    def test_run_with_none_context(self):
        agent = ForecastingAgent()
        result = agent.run(None)
        self.assertEqual(result['agent'], 'forecasting_agent')


class PurchasingAgentComprehensiveTest(TestCase):
    def _build_agent(self, email_succeed=True, confirm_after=0):
        purchasing_service = FakePurchasingService()
        workflow_service = FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(),
            email_send_tool=FakeEmailSendTool(succeed=email_succeed),
            confirmation_tool=FakeConfirmationTool(confirm_after=confirm_after),
            purchasing_service=purchasing_service,
            workflow_service=workflow_service,
            initial_delay=0.0,
            max_delay=0.0,
            max_attempts=3,
            sleep_fn=lambda x: None,
        )
        return agent, purchasing_service, workflow_service

    def test_initialization(self):
        agent = PurchasingAgent()
        self.assertIsNotNone(agent.po_draft_tool)
        self.assertIsNotNone(agent.email_send_tool)
        self.assertIsNotNone(agent.confirmation_tool)

    def test_full_workflow_auto_approve(self):
        agent, purchasing_service, workflow_service = self._build_agent(confirm_after=0)
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'user_id': 1,
                'auto_approve': True,
            }
        )
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['agent'], 'purchasing_agent')
        self.assertIn('po_id', result)

    def test_pending_approval_without_callback(self):
        agent, _, workflow_service = self._build_agent()
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
            }
        )
        self.assertEqual(result['status'], 'pending_approval')

    def test_rejection_via_callback(self):
        agent, purchasing_service, workflow_service = self._build_agent()
        user = SimpleNamespace(id=1)
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'user': user,
                'approval_callback': lambda po_id: False,
            }
        )
        self.assertEqual(result['status'], 'rejected')
        self.assertTrue(len(purchasing_service.rejected) > 0)

    def test_approval_via_callback(self):
        agent, purchasing_service, workflow_service = self._build_agent(confirm_after=0)
        user = SimpleNamespace(id=1)
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'user': user,
                'approval_callback': lambda po_id: True,
            }
        )
        self.assertEqual(result['status'], 'confirmed')
        self.assertIn(100, purchasing_service.approved)

    def test_email_failure(self):
        agent, purchasing_service, workflow_service = self._build_agent(email_succeed=False)
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'auto_approve': True,
            }
        )
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['step'], 'email_send')

    def test_draft_failure(self):
        agent, _, _ = self._build_agent()
        agent.po_draft_tool = SimpleNamespace(
            run=lambda input: {'status': 'failed', 'error': 'DB error'}
        )
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
            }
        )
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['step'], 'draft')

    def test_workflow_status_transitions(self):
        agent, _, workflow_service = self._build_agent(confirm_after=0)
        agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'auto_approve': True,
            }
        )
        statuses = [s for _, s in workflow_service.statuses]
        self.assertIn(PurchaseOrderWorkflow.Status.PENDING_APPROVAL, statuses)
        self.assertIn(PurchaseOrderWorkflow.Status.APPROVED, statuses)

    def test_trace_spans_recorded(self):
        agent, _, _ = self._build_agent(confirm_after=0)
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'auto_approve': True,
            }
        )
        self.assertIn('po_id', result)

    def test_timeout_after_max_attempts(self):
        agent, _, workflow_service = self._build_agent()
        agent.confirmation_tool = SimpleNamespace(
            run=lambda input: {'confirmed': False, 'status': 'waiting_confirmation'}
        )
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'auto_approve': True,
            }
        )
        self.assertEqual(result['status'], 'timeout')
        self.assertEqual(result['polling_attempts'], 3)

    def test_terminal_status_on_rejection(self):
        agent, _, _ = self._build_agent()
        agent.confirmation_tool = SimpleNamespace(
            run=lambda input: {'confirmed': False, 'status': 'rejected', 'terminal': True}
        )
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
                'auto_approve': True,
            }
        )
        self.assertEqual(result['status'], 'failed')
        self.assertIn('terminal status', result['error'])

    def test_exception_handling(self):
        agent, _, _ = self._build_agent()
        agent.po_draft_tool = SimpleNamespace(
            run=lambda input: (_ for _ in ()).throw(Exception('boom'))
        )
        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 10,
                'supplier_id': 1,
            }
        )
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)
