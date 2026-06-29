"""Tests for AgentPipelineOrchestrator."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.forecasting.pipeline_orchestrator import AgentPipelineOrchestrator


class _FakeRunRecord:
    def __init__(self):
        self.status = 'running'
        self.output_data = None

    def save(self, update_fields=None):
        pass


class AgentPipelineOrchestratorInitTest(TestCase):
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_init_default(self, mock_po_cls, mock_da_cls):
        orchestrator = AgentPipelineOrchestrator()
        self.assertIsNone(orchestrator.system_user_id)

    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_init_with_user_id(self, mock_po_cls, mock_da_cls):
        orchestrator = AgentPipelineOrchestrator(system_user_id=42)
        self.assertEqual(orchestrator.system_user_id, 42)
        mock_po_cls.assert_called_once_with(system_user_id=42)


class AgentPipelineOrchestratorRunTest(TestCase):
    @patch('apps.forecasting.pipeline_orchestrator.AgentRun.objects')
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_run_no_skus(self, mock_po_cls, mock_da_cls, mock_run_objs):
        mock_run_objs.create.return_value = _FakeRunRecord()
        orchestrator = AgentPipelineOrchestrator()
        orchestrator._run_forecast_step = MagicMock(return_value={'dispatched': 0})
        result = orchestrator.run()
        self.assertEqual(result['forecast']['dispatched'], 0)

    @patch('apps.forecasting.pipeline_orchestrator.AgentRun.objects')
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_run_with_skus(self, mock_po_cls, mock_da_cls, mock_run_objs):
        mock_run_objs.create.return_value = _FakeRunRecord()
        orchestrator = AgentPipelineOrchestrator()
        orchestrator._run_forecast_step = MagicMock(
            return_value={'dispatched': 2, 'sku_ids': [100, 200]}
        )
        orchestrator._run_decision_step = MagicMock(
            return_value={'skus_processed': 2, 'reorder_flags_created': 1, 'errors': []}
        )
        orchestrator._run_po_creation_step = MagicMock(
            return_value={'created': 1, 'skipped_no_supplier': 0, 'failed': 0, 'errors': []}
        )
        result = orchestrator.run()
        self.assertEqual(result['forecast']['dispatched'], 2)
        self.assertEqual(result['decision']['skus_processed'], 2)
        self.assertEqual(result['po_creation']['created'], 1)

    @patch('apps.forecasting.pipeline_orchestrator.AgentRun.objects')
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_run_exception_sets_failed(self, mock_po_cls, mock_da_cls, mock_run_objs):
        fake_record = _FakeRunRecord()
        mock_run_objs.create.return_value = fake_record
        orchestrator = AgentPipelineOrchestrator()
        orchestrator._run_forecast_step = MagicMock(side_effect=RuntimeError('boom'))
        with self.assertRaises(RuntimeError):
            orchestrator.run()
        self.assertEqual(fake_record.status, 'failed')


class AgentPipelineOrchestratorForecastStepTest(TestCase):
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_empty_skus(self, mock_po_cls, mock_da_cls):

        orchestrator = AgentPipelineOrchestrator()
        with patch('apps.inventory.models.SKU') as mock_sku_cls:
            mock_sku_cls.objects.filter.return_value.values_list.return_value = []
            result = orchestrator._run_forecast_step()
            self.assertEqual(result, {'dispatched': 0})


class AgentPipelineOrchestratorDecisionStepTest(TestCase):
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_empty_skus(self, mock_po_cls, mock_da_cls):
        orchestrator = AgentPipelineOrchestrator()
        result = orchestrator._run_decision_step([])
        self.assertEqual(result['skus_processed'], 0)

    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_with_sku_ids(self, mock_po_cls, mock_da_cls):
        mock_da_cls.return_value.evaluate_sku.return_value = {
            'sku_id': 100,
            'reorder_flag_id': 1,
        }
        orchestrator = AgentPipelineOrchestrator()
        result = orchestrator._run_decision_step([100])
        self.assertEqual(result['skus_processed'], 1)
        self.assertEqual(result['reorder_flags_created'], 1)

    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_exception_in_evaluate(self, mock_po_cls, mock_da_cls):
        mock_da_cls.return_value.evaluate_sku.side_effect = RuntimeError('boom')
        orchestrator = AgentPipelineOrchestrator()
        result = orchestrator._run_decision_step([100])
        self.assertEqual(result['skus_processed'], 1)
        self.assertEqual(len(result['errors']), 1)


class AgentPipelineOrchestratorPOCreationStepTest(TestCase):
    @patch('apps.forecasting.pipeline_orchestrator.ReorderFlag.objects')
    @patch('apps.forecasting.pipeline_orchestrator.DecisionAgent')
    @patch('apps.forecasting.pipeline_orchestrator.POFromFlagCreator')
    def test_no_open_flags(self, mock_po_cls, mock_da_cls, mock_flag_objs):
        mock_flag_objs.filter.return_value.select_related.return_value = []
        mock_po = MagicMock()
        mock_po.process_flags.return_value = {
            'created': 0,
            'skipped_no_supplier': 0,
            'failed': 0,
            'errors': [],
        }
        mock_po_cls.return_value = mock_po
        orchestrator = AgentPipelineOrchestrator()
        result = orchestrator._run_po_creation_step()
        self.assertEqual(result['created'], 0)
