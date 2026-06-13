<<<<<<< HEAD
"""Remaining coverage tests — 12 tests covering three known gaps.

Problem 1: DecisionAgent tests (9) — must work without live LLM API.
Problem 2: StubToolTests (2) — EmailSendTool, PODraftTool response formats.
Problem 3: PurchasingAgentTests (1) — tool must handle 'action' trace key.
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from ai.agents.decision_agent import DecisionAgent, DecisionReasoner
from ai.agents.purchasing_agent import PurchasingAgent
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.po_draft import PODraftTool

# ---------------------------------------------------------------------------
# Fakes (same style as test_agent_integration_comprehensive.py)
# ---------------------------------------------------------------------------


class _FakeStockTool:
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


class _FakeForecastTool:
    name = 'forecast_read_tool'

    def __init__(self, total_predicted_demand=30.0):
        self.total_predicted_demand = total_predicted_demand

    def run(self, input):
        return {
            'sku_code': 'SKU-001',
            'forecast_days': int(input.get('forecast_days', 7)),
            'total_predicted_demand': self.total_predicted_demand,
        }


class _FakePOStatusTool:
    name = 'po_status_check_tool'

    def __init__(self, has_open_po=False, open_po_id=None):
        self.has_open_po = has_open_po
        self.open_po_id = open_po_id

    def run(self, input):
        return {'has_open_po': self.has_open_po, 'open_po_id': self.open_po_id}


class _FakeForecastingService:
    def __init__(self):
        self.persisted = []

    def persist_reorder_flag(self, decision):
        self.persisted.append(decision)
        return SimpleNamespace(id=77)


class _FakeReasoner:
    def generate(self, payload):
        return (
            f'Stock {payload["quantity_available"]} vs demand {payload["total_predicted_demand"]}.'
        )


class _FakePODraftTool:
    def __init__(self):
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        if input.get('action') == 'trace':
            return {'status': 'traced'}
        return {'po_id': 100, 'status': 'draft', 'sku_id': 1, 'supplier_id': 1, 'quantity': 10}


class _FakeEmailSendTool:
    def __init__(self, succeed=True):
        self.succeed = succeed

    def run(self, input):
        if self.succeed:
            return {'status': 'sent', 'po_id': input['po_id'], 'message_id': 'msg-123'}
        return {'status': 'failed', 'error': 'SMTP error'}


class _FakeConfirmationTool:
    def __init__(self, confirm_after=0):
        self.confirm_after = confirm_after
        self.call_count = 0

    def run(self, input):
        self.call_count += 1
        if self.call_count > self.confirm_after:
            return {'confirmed': True, 'po_id': input['po_id']}
        return {'confirmed': False, 'po_id': input['po_id'], 'status': 'waiting_confirmation'}


class _FakePurchasingService:
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


class _FakeWorkflowService:
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


# ===================================================================
# Problem 1 — DecisionAgent / DecisionReasoner (9 tests)
# ===================================================================


class DecisionReasonerOfflineTest(TestCase):
    """Verify DecisionReasoner works without a live LLM API call."""

    def test_generate_returns_string(self):
        reasoner = DecisionReasoner()
        payload = {
            'quantity_available': 10,
            'total_predicted_demand': 50,
            'lead_time_days': 7,
            'safety_stock': 5,
        }
        with patch('ai.llm.chain.get_llm', side_effect=Exception('no live API')):
            result = reasoner.generate(payload)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_generate_fallback_contains_numbers(self):
        reasoner = DecisionReasoner()
        payload = {
            'quantity_available': 10,
            'total_predicted_demand': 50,
            'lead_time_days': 7,
            'safety_stock': 5,
        }
        with patch('ai.llm.chain.get_llm', side_effect=Exception('no live API')):
            result = reasoner.generate(payload)
        self.assertIn('10', result)
        self.assertIn('50', result)

    def test_generate_with_custom_llm(self):
        payload = {
            'quantity_available': 10,
            'total_predicted_demand': 50,
            'lead_time_days': 7,
            'safety_stock': 5,
        }

        class _FakePromptChain:
            def __or__(self, other):
                return self

            def invoke(self, x, config=None):
                return 'Custom reasoning output'

        with patch('ai.agents.decision_agent.ChatPromptTemplate') as mock_tpl:
            mock_tpl.from_messages.return_value = _FakePromptChain()
            reasoner = DecisionReasoner(llm=object())
            result = reasoner.generate(payload)
        self.assertIn('Custom reasoning output', result)


class DecisionAgentOfflineTest(TestCase):
    """Verify DecisionAgent works with default tools and offline reasoner."""

    def _build_agent(self, quantity_available=50, total_predicted_demand=30.0, has_open_po=False):
        service = _FakeForecastingService()
        return DecisionAgent(
            stock_tool=_FakeStockTool(quantity_available=quantity_available),
            forecast_tool=_FakeForecastTool(total_predicted_demand),
            po_status_tool=_FakePOStatusTool(has_open_po=has_open_po),
            forecasting_service=service,
            reasoner=_FakeReasoner(),
        ), service

    def test_single_product_low_stock(self):
        agent, service = self._build_agent(quantity_available=5, total_predicted_demand=62)
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        self.assertTrue(decision['reorder_required'])
        self.assertEqual(result['flags_created'], 1)
        self.assertTrue(len(service.persisted) > 0)

    def test_single_product_sufficient_stock(self):
        agent, service = self._build_agent(quantity_available=200, total_predicted_demand=30)
        result = agent.run({'product_id': 1})
        decision = result['results'][0]
        self.assertFalse(decision['reorder_required'])
        self.assertEqual(result['flags_created'], 0)
        self.assertEqual(service.persisted, [])

    def test_multiple_products(self):
        agent, _ = self._build_agent(quantity_available=5, total_predicted_demand=62)
        result = agent.run({'product_ids': [1, 2, 3]})
        self.assertEqual(len(result['results']), 3)
        self.assertEqual(result['flags_created'], 3)

    def test_empty_context(self):
        agent, _ = self._build_agent()
        result = agent.run({})
        self.assertEqual(result['results'], [])
        self.assertEqual(result['flags_created'], 0)

    def test_tool_tracing(self):
        agent, _ = self._build_agent()
        trace_spans = []
        agent.evaluate_product(1, trace_spans=trace_spans)
        self.assertGreater(len(trace_spans), 0)
        span_names = [s['name'] for s in trace_spans]
        self.assertIn('stock_level_read_tool', span_names)
        self.assertIn('forecast_read_tool', span_names)


# ===================================================================
# Problem 2 — StubToolTests (2 tests)
# ===================================================================


class StubToolTests(TestCase):
    def test_email_send_returns_sent(self):
        """EmailSendTool must return status 'sent' after dispatch."""

        class _FakeService:
            repo = SimpleNamespace(
                get_by_id=lambda po_id: SimpleNamespace(
                    id=po_id,
                    status='approved',
                    sku=SimpleNamespace(code='SKU-1', product=SimpleNamespace(name='Widget')),
                    supplier=SimpleNamespace(name='Acme', contact_email='a@b.com'),
                    quantity=10,
                    total_cost='100.00',
                    requested_by=SimpleNamespace(name='Test'),
                )
            )

        tool = EmailSendTool(purchasing_service=_FakeService())

        class _FakeTask:
            id = 'task-abc'

        with patch('ai.agents.tools.email_send.send_email_with_retry') as m:
            m.delay.return_value = _FakeTask()
            result = tool.run({'po_id': 1})

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['po_id'], 1)
        self.assertIn('message_id', result)

    def test_po_draft_returns_draft(self):
        """PODraftTool must return status 'draft' for valid input."""

        class _FakeService:
            repo = SimpleNamespace(
                create=lambda data: SimpleNamespace(
                    id=42, status='draft', sku_id=1, supplier_id=5, quantity=100
                )
            )

        tool = PODraftTool(service=_FakeService())
        result = tool.run(
            {
                'sku_id': '1',
                'quantity': '100',
                'supplier_id': '5',
            }
        )
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['po_id'], 42)


# ===================================================================
# Problem 3 — PurchasingAgent (1 test)
# ===================================================================


class PurchasingAgentTraceActionTest(TestCase):
    """PurchasingAgent must not crash when a tool receives an 'action' key."""

    def test_po_draft_tool_handles_trace_action(self):
        """PODraftTool must not KeyError when called with {'action': 'trace'}."""
        tool = PODraftTool(service=SimpleNamespace(repo=SimpleNamespace()))
        result = tool.run({'action': 'trace', 'step': 'approval_rejected'})
        self.assertIn('status', result)

    def test_purchasing_agent_rejection_no_keyerror(self):
        """Full rejection path must return 'rejected', not crash with KeyError."""
        purchasing_service = _FakePurchasingService()
        workflow_service = _FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=_FakePODraftTool(),
            email_send_tool=_FakeEmailSendTool(),
            confirmation_tool=_FakeConfirmationTool(),
            purchasing_service=purchasing_service,
            workflow_service=workflow_service,
            initial_delay=0.0,
            max_delay=0.0,
            max_attempts=1,
            sleep_fn=lambda x: None,
        )
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
        self.assertIn('po_id', result)
=======
import unittest
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.agents.forecasting_agent import ForecastingAgent
from ai.agents.purchasing_agent import PurchasingAgent
from ai.agents.tools.confirmation_listener import ConfirmationListenerTool
from ai.agents.tools.db_read import DBReadTool
from ai.agents.tools.db_update import DBUpdateTool
from ai.agents.tools.db_write import DBWriteTool
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.po_draft import PODraftTool
from ai.rag.citation import inject_citations


class StubToolTests(unittest.TestCase):
    def test_confirmation_listener_returns_false(self):
        tool = ConfirmationListenerTool()
        self.assertFalse(tool.run({'order_id': 1})['confirmed'])

    def test_db_read_returns_empty(self):
        tool = DBReadTool()
        self.assertEqual(tool.run({'query': 'all'}), {'data': []})

    def test_db_update_returns_status(self):
        tool = DBUpdateTool()
        self.assertEqual(tool.run({'id': 1}), {'status': 'updated'})

    def test_db_write_returns_status(self):
        tool = DBWriteTool()
        self.assertEqual(tool.run({'payload': {}}), {'status': 'written'})

    def test_email_send_returns_sent(self):
        tool = EmailSendTool()
        self.assertEqual(tool.run({'to': 'x@y.com'}), {'status': 'sent'})

    def test_po_draft_returns_draft(self):
        tool = PODraftTool()
        self.assertEqual(tool.run({'sku': 'X'}), {'po_id': None, 'status': 'draft'})


class BaseToolInvokeTests(unittest.TestCase):
    def test_invoke_empty_input(self):
        tool = DBReadTool()
        result = tool.invoke({})
        self.assertIn('data', result)

    def test_invoke_none_input(self):
        tool = DBReadTool()
        result = tool.invoke(None)
        self.assertIn('data', result)

    def test_as_langchain_tool(self):
        tool = DBReadTool()
        lc_tool = tool.as_langchain_tool()
        self.assertEqual(lc_tool.name, 'db_read_tool')


class ForecastingAgentTests(unittest.TestCase):
    @patch('ai.agents.forecasting_agent.trace_agent_run')
    def test_run_returns_not_implemented(self, mock_trace):
        agent = ForecastingAgent()
        result = agent.run()
        self.assertEqual(result['status'], 'not_implemented')
        self.assertEqual(result['agent'], 'forecasting_agent')
        mock_trace.assert_called_once()

    @patch('ai.agents.forecasting_agent.trace_agent_run')
    def test_run_with_context(self, mock_trace):
        agent = ForecastingAgent()
        result = agent.run(context={'key': 'val'})
        self.assertEqual(result['agent'], 'forecasting_agent')


class PurchasingAgentTests(unittest.TestCase):
    @patch('ai.agents.purchasing_agent.trace_agent_run')
    def test_run_returns_draft_po(self, mock_trace):
        agent = PurchasingAgent()
        result = agent.run(context={'sku': 'X'})
        self.assertEqual(result['action'], 'draft_po')
        mock_trace.assert_called_once()


class CitationTests(unittest.TestCase):
    def test_inject_citations_returns_response(self):
        result = inject_citations('answer', [{'source': 'doc.pdf'}])
        self.assertEqual(result, 'answer')

    def test_inject_citations_empty_sources(self):
        result = inject_citations('hello', [])
        self.assertEqual(result, 'hello')


class IntentClassifierTests(unittest.TestCase):
    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_nl_query(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"intent": "nl_query", "confidence": 0.95}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('show me all products')
        self.assertEqual(result.intent, 'nl_query')
        self.assertAlmostEqual(result.confidence, 0.95)

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_rag(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"intent": "rag", "confidence": 0.88}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('what is the return policy')
        self.assertEqual(result.intent, 'rag')

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_out_of_scope(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"intent": "out_of_scope", "confidence": 0.7}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('tell me a joke')
        self.assertEqual(result.intent, 'out_of_scope')

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_unknown_defaults_to_nl_query(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"intent": "unknown_intent", "confidence": 0.5}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('random')
        self.assertEqual(result.intent, 'nl_query')
        self.assertEqual(result.confidence, 0.5)

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_json_parse_error(self, mock_llm, mock_invoke):
        mock_invoke.return_value = 'not json'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('bad response')
        self.assertEqual(result.intent, 'nl_query')
        self.assertEqual(result.confidence, 0.5)

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_generic_exception(self, mock_llm, mock_invoke):
        mock_invoke.side_effect = RuntimeError('network down')
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('query')
        self.assertEqual(result.intent, 'nl_query')
        self.assertEqual(result.confidence, 0.5)

    @patch('ai.llm.intent_classifier.os.getenv', return_value=None)
    def test_get_classifier_llm_missing_key(self, mock_getenv):
        import ai.llm.intent_classifier as mod

        mod._ClassifierLLM = None
        with self.assertRaises(ValueError):
            mod._get_classifier_llm()
        mod._ClassifierLLM = None

    @patch('ai.llm.intent_classifier.ChatOpenAI')
    @patch('ai.llm.intent_classifier.os.getenv', return_value='test-key')
    def test_get_classifier_llm_caches(self, mock_getenv, mock_cls):
        import ai.llm.intent_classifier as mod

        mod._ClassifierLLM = None
        llm1 = mod._get_classifier_llm()
        llm2 = mod._get_classifier_llm()
        self.assertIs(llm1, llm2)
        mock_cls.assert_called_once()
        mod._ClassifierLLM = None

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_missing_confidence(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"intent": "rag"}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('policy')
        self.assertEqual(result.intent, 'rag')
        self.assertEqual(result.confidence, 0.5)

    @patch('ai.llm.intent_classifier.invoke_with_langfuse')
    @patch('ai.llm.intent_classifier._get_classifier_llm')
    def test_classify_intent_missing_intent_key(self, mock_llm, mock_invoke):
        mock_invoke.return_value = '{"confidence": 0.9}'
        from ai.llm.intent_classifier import classify_intent

        result = classify_intent('query')
        self.assertEqual(result.intent, 'nl_query')


class PurgeOldAuditLogsTests(TestCase):
    @patch('apps.audit.models.AuditLog')
    @patch('apps.audit.tasks.timezone')
    def test_purge_deletes_old_logs(self, mock_timezone, mock_audit_model):
        mock_timezone.now.return_value = MagicMock()
        mock_audit_model.objects.filter.return_value.delete.return_value = (5, {})
        from apps.audit.tasks import purge_old_audit_logs

        result = purge_old_audit_logs()
        self.assertEqual(result['deleted'], 5)

    @patch('apps.audit.models.AuditLog')
    @patch('apps.audit.tasks.timezone')
    def test_purge_no_old_logs(self, mock_timezone, mock_audit_model):
        mock_timezone.now.return_value = MagicMock()
        mock_audit_model.objects.filter.return_value.delete.return_value = (0, {})
        from apps.audit.tasks import purge_old_audit_logs

        result = purge_old_audit_logs()
        self.assertEqual(result['deleted'], 0)


class IngestDocumentCommandTests(TestCase):
    @patch('apps.ingestion.management.commands.ingest_document.ingest_pdf')
    @patch('apps.ingestion.management.commands.ingest_document.time')
    def test_handle_success(self, mock_time, mock_ingest):
        mock_time.time.side_effect = [0, 1.5]
        mock_ingest.return_value = {
            'filename': 'test.pdf',
            'pages': 5,
            'chunks': 20,
            'api_calls': 2,
        }
        from django.core.management import call_command

        call_command('ingest_document', file='test.pdf')

    @patch('apps.ingestion.management.commands.ingest_document.ingest_pdf')
    def test_handle_failure(self, mock_ingest):
        mock_ingest.side_effect = RuntimeError('bad file')
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command('ingest_document', file='bad.pdf')
>>>>>>> main
