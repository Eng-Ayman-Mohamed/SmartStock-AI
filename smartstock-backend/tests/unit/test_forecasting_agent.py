import unittest
from unittest.mock import MagicMock, patch

import pandas as pd


class TestForecastDBReadTool(unittest.TestCase):
    def setUp(self):
        from ai.agents.tools.forecast_db_read import ForecastDBReadTool

        self.tool = ForecastDBReadTool

    def test_run_with_valid_data(self):
        mock_repo = MagicMock()
        with patch(
            'ai.agents.tools.forecast_db_read.prepare_forecast_dataframe'
        ) as mock_prepare:
            mock_df = pd.DataFrame(
                {'ds': pd.to_datetime(['2025-01-01', '2025-01-02']), 'y': [10.0, 20.0]}
            )
            mock_prepare.return_value = mock_df

            tool = self.tool(repo=mock_repo)
            result = tool.run({'sku_id': 1, 'sku_code': 'SKU001'})

        self.assertTrue(result['has_data'])
        self.assertEqual(result['record_count'], 2)
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['ds'], '2025-01-01')
        self.assertEqual(result['data'][0]['y'], 10.0)

    def test_run_with_no_data(self):
        mock_repo = MagicMock()
        with patch(
            'ai.agents.tools.forecast_db_read.prepare_forecast_dataframe'
        ) as mock_prepare:
            mock_prepare.return_value = None

            tool = self.tool(repo=mock_repo)
            result = tool.run({'sku_id': 1, 'sku_code': 'SKU001'})

        self.assertFalse(result['has_data'])
        self.assertEqual(result['record_count'], 0)

    def test_run_with_empty_dataframe(self):
        mock_repo = MagicMock()
        with patch(
            'ai.agents.tools.forecast_db_read.prepare_forecast_dataframe'
        ) as mock_prepare:
            mock_prepare.return_value = pd.DataFrame(
                {'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')}
            )

            tool = self.tool(repo=mock_repo)
            result = tool.run({'sku_id': 1, 'sku_code': 'SKU001'})

        self.assertFalse(result['has_data'])
        self.assertEqual(result['record_count'], 0)


class TestProphetRunTool(unittest.TestCase):
    def setUp(self):
        from ai.agents.tools.prophet_run import ProphetRunTool

        self.tool = ProphetRunTool

    def test_run_with_data(self):
        mock_engine = MagicMock()
        mock_engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': '2025-02-01',
                    'predicted_quantity': 15.0,
                    'lower_bound': 12.0,
                    'upper_bound': 18.0,
                }
            ],
            'model_version': 'prophet_1.1',
            'forecast_method': 'prophet',
            'mae': 2.5,
            'mape': 0.15,
        }

        tool = self.tool(engine=mock_engine)
        result = tool.run(
            {
                'sku_id': 1,
                'sku_code': 'SKU001',
                'data': [{'ds': '2025-01-01', 'y': 10.0}],
                'periods': 30,
            }
        )

        self.assertEqual(result['sku_id'], 1)
        self.assertEqual(result['forecast_days'], 1)
        self.assertEqual(result['model_version'], 'prophet_1.1')
        mock_engine.predict.assert_called_once()

    def test_run_with_empty_data(self):
        mock_engine = MagicMock()
        mock_engine.predict.return_value = {
            'results': [],
            'model_version': 'moving_average_fallback',
            'forecast_method': 'moving_average',
            'mae': None,
            'mape': None,
        }

        tool = self.tool(engine=mock_engine)
        result = tool.run(
            {
                'sku_id': 1,
                'sku_code': 'SKU001',
                'data': [],
                'periods': 30,
            }
        )

        self.assertEqual(result['forecast_days'], 0)
        self.assertEqual(result['model_version'], 'moving_average_fallback')


class TestForecastDBWriteTool(unittest.TestCase):
    def setUp(self):
        from ai.agents.tools.forecast_db_write import ForecastDBWriteTool

        self.tool = ForecastDBWriteTool

    def test_run_writes_records(self):
        mock_repo = MagicMock()
        mock_repo.has_todays_forecast.return_value = False

        tool = self.tool(repo=mock_repo)
        result = tool.run(
            {
                'sku_id': 1,
                'sku_code': 'SKU001',
                'results': [
                    {
                        'forecast_date': '2025-02-01',
                        'predicted_quantity': 15.0,
                        'lower_bound': 12.0,
                        'upper_bound': 18.0,
                    }
                ],
                'model_version': 'prophet_1.1',
                'mae': 2.5,
                'mape': 0.15,
            }
        )

        self.assertEqual(result['status'], 'written')
        self.assertEqual(result['records_written'], 1)
        mock_repo.upsert.assert_called_once()
        mock_repo.has_todays_forecast.assert_called_once_with(1)

    def test_run_skips_when_todays_forecast_exists(self):
        mock_repo = MagicMock()
        mock_repo.has_todays_forecast.return_value = True

        tool = self.tool(repo=mock_repo)
        result = tool.run(
            {
                'sku_id': 1,
                'sku_code': 'SKU001',
                'results': [{'forecast_date': '2025-02-01', 'predicted_quantity': 15.0}],
                'model_version': 'prophet_1.1',
            }
        )

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'todays_forecast_exists')
        self.assertEqual(result['records_written'], 0)
        mock_repo.upsert.assert_not_called()


class TestForecastingAgent(unittest.TestCase):
    def setUp(self):
        from ai.agents.forecasting_agent import ForecastingAgent

        self.agent_class = ForecastingAgent

    def test_initialization(self):
        agent = self.agent_class()
        self.assertIsNotNone(agent.read_tool)
        self.assertIsNotNone(agent.prophet_tool)
        self.assertIsNotNone(agent.write_tool)

    def test_initialization_with_custom_tools(self):
        mock_read = MagicMock()
        mock_prophet = MagicMock()
        mock_write = MagicMock()

        agent = self.agent_class(
            read_tool=mock_read,
            prophet_tool=mock_prophet,
            write_tool=mock_write,
        )

        self.assertIs(agent.read_tool, mock_read)
        self.assertIs(agent.prophet_tool, mock_prophet)
        self.assertIs(agent.write_tool, mock_write)

    @patch('ai.agents.forecasting_agent.trace_agent_run')
    def test_run_empty_skus(self, mock_trace):
        mock_repo = MagicMock()
        mock_repo.get_all_skus.return_value = []

        agent = self.agent_class(repo=mock_repo)
        result = agent.run()

        self.assertEqual(result['agent'], 'forecasting_agent')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['total_skus'], 0)
        mock_trace.assert_called_once()

    @patch('ai.agents.forecasting_agent.trace_agent_run')
    def test_run_skips_when_todays_forecast_exists(self, mock_trace):
        mock_repo = MagicMock()
        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.code = 'SKU001'
        mock_repo.get_all_skus.return_value = [mock_sku]
        mock_repo.get_sku.return_value = mock_sku
        mock_repo.has_todays_forecast.return_value = True

        agent = self.agent_class(repo=mock_repo)
        result = agent.run()

        self.assertEqual(result['total_skus'], 1)
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(result['results'][0]['reason'], 'todays_forecast_exists')

    @patch('ai.agents.forecasting_agent.trace_agent_run')
    @patch('ai.agents.forecasting_agent.get_langchain_callbacks')
    def test_run_fails_gracefully_on_agent_error(self, mock_callbacks, mock_trace):
        mock_callbacks.return_value = []
        mock_repo = MagicMock()
        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.code = 'SKU001'
        mock_repo.get_sku.return_value = mock_sku
        mock_repo.has_todays_forecast.return_value = False

        agent = self.agent_class(
            repo=mock_repo,
            agent_factory=lambda model, tools, system_prompt: _raise_on_invoke(Exception('LLM unavailable')),
        )
        result = agent.run({'sku_ids': [1]})

        self.assertEqual(result['total_skus'], 1)
        self.assertEqual(result['failed'], 1)
        self.assertIn('error', result['results'][0])

    @patch('ai.agents.forecasting_agent.trace_agent_run')
    @patch('ai.agents.forecasting_agent.get_langchain_callbacks')
    def test_run_with_single_sku(self, mock_callbacks, mock_trace):
        mock_callbacks.return_value = []
        mock_repo = MagicMock()
        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.code = 'SKU001'
        mock_repo.get_sku.return_value = mock_sku
        mock_repo.has_todays_forecast.return_value = False

        mock_read = MagicMock()
        mock_read.name = 'forecast_db_read_tool'
        mock_read.description = 'Reads historical sales data.'
        mock_read.args_schema = None

        mock_prophet = MagicMock()
        mock_prophet.name = 'prophet_run_tool'
        mock_prophet.description = 'Runs Prophet model.'
        mock_prophet.args_schema = None

        mock_write = MagicMock()
        mock_write.name = 'forecast_db_write_tool'
        mock_write.description = 'Writes forecast results.'
        mock_write.args_schema = None

        agent = self.agent_class(
            repo=mock_repo,
            read_tool=mock_read,
            prophet_tool=mock_prophet,
            write_tool=mock_write,
            agent_factory=_make_success_agent_factory(),
        )
        result = agent.run({'sku_ids': [1]})

        self.assertEqual(result['total_skus'], 1)
        self.assertEqual(result['processed'], 1)
        self.assertEqual(result['status'], 'completed')

    def test_extract_sku_ids_from_context(self):
        mock_repo = MagicMock()
        agent = self.agent_class(repo=mock_repo)

        ids = agent._extract_sku_ids({'sku_id': 5})
        self.assertEqual(ids, [5])

        ids = agent._extract_sku_ids({'sku_ids': [1, 2, 3]})
        self.assertEqual(ids, [1, 2, 3])


class TestForecastingAgentExecutionError(unittest.TestCase):
    def test_exception(self):
        from ai.agents.forecasting_agent import ForecastingAgentExecutionError

        exc = ForecastingAgentExecutionError('test error')
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), 'test error')


# --- Helpers ---


def _raise_on_invoke(exception):
    class FailingAgent:
        def invoke(self, input, config=None):
            raise exception

    return FailingAgent()


def _make_success_agent_factory():
    class SucceedingAgent:
        def invoke(self, input, config=None):
            return {'messages': [MagicMock(content='done')]}

    return lambda model, tools, system_prompt: SucceedingAgent()
