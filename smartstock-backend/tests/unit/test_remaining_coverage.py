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
        mock_service = MagicMock()
        mock_service.check_confirmation.return_value = {'confirmed': False, 'timed_out': False}
        tool = ConfirmationListenerTool(service=mock_service)
        self.assertFalse(tool.run({'po_id': 1})['confirmed'])

    def test_db_read_returns_empty(self):
        tool = DBReadTool()
        self.assertEqual(tool.run({'query': 'all'}), {'data': []})

    def test_db_update_returns_status(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.id = 1
        mock_po.status = 'updated'
        mock_service.transition_po_status.return_value = mock_po
        tool = DBUpdateTool(service=mock_service)
        result = tool.run({'po_id': 1, 'status': 'updated'})
        self.assertEqual(result, {'po_id': 1, 'status': 'updated'})

    def test_db_write_returns_status(self):
        tool = DBWriteTool()
        self.assertEqual(tool.run({'payload': {}}), {'status': 'written'})

    def test_email_send_returns_sent(self):
        mock_service = MagicMock()
        mock_service.send_po_email.return_value = {'sent': True, 'recipient': 'x@y.com'}
        tool = EmailSendTool(service=mock_service)
        self.assertEqual(tool.run({'po_id': 1}), {'sent': True, 'recipient': 'x@y.com'})

    def test_po_draft_returns_draft(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.id = 1
        mock_service.draft_po.return_value = mock_po
        mock_sku = MagicMock()
        mock_product = MagicMock()
        mock_product.unit_price = 10.0
        mock_sku.product = mock_product
        with (
            patch('ai.agents.tools.po_draft.generate_po_number', return_value='PO-001'),
            patch('ai.agents.tools.po_draft.SKU.objects.select_related') as mock_sr,
        ):
            mock_sr.return_value.get.return_value = mock_sku
            tool = PODraftTool(service=mock_service)
            result = tool.run({'sku_id': 1, 'quantity': 5, 'supplier_id': 1})
            self.assertEqual(result['status'], 'draft')
            self.assertEqual(result['po_id'], 1)


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
