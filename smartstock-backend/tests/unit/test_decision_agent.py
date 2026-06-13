from types import SimpleNamespace

from ai.agents.decision_agent import DecisionAgent


class FakeStockTool:
    def __init__(self, quantity_available):
        self.quantity_available = quantity_available

    def run(self, input):
        return {
            'product_id': int(input['product_id']),
            'sku_code': 'SKU-001',
            'quantity_available': self.quantity_available,
            'reorder_point': 20,
            'lead_time_days': 7,
            'safety_stock': 10,
        }


class FakeForecastTool:
    def __init__(self, total_predicted_demand):
        self.total_predicted_demand = total_predicted_demand
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        return {
            'sku_code': 'SKU-001',
            'forecast_days': int(input['forecast_days']),
            'total_predicted_demand': self.total_predicted_demand,
        }


class FakePOStatusTool:
    def __init__(self, has_open_po=False, open_po_id=None):
        self.has_open_po = has_open_po
        self.open_po_id = open_po_id

    def run(self, input):
        return {
            'has_open_po': self.has_open_po,
            'open_po_id': self.open_po_id,
        }


class FakeForecastingService:
    def __init__(self):
        self.persisted = []

    def persist_reorder_flag(self, decision):
        self.persisted.append(decision)
        return SimpleNamespace(id=77)


class FakeReasoner:
    def generate(self, payload):
        return (
            f'Current stock of {payload["quantity_available"]} units is compared with '
            f'predicted demand of {payload["total_predicted_demand"]} units over '
            f'{payload["lead_time_days"]} days plus safety stock of {payload["safety_stock"]} units.'
        )


class FakeLangChainDecisionAgent:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    def invoke(self, input, config=None):
        product_id = 1
        stock = self.tools['stock_level_read_tool'].invoke({'product_id': product_id})
        self.tools['forecast_read_tool'].invoke(
            {'product_id': product_id, 'forecast_days': stock['lead_time_days']}
        )
        self.tools['po_status_check_tool'].invoke({'product_id': product_id})
        return {'messages': [SimpleNamespace(content='observations gathered')]}


def fake_agent_factory(model, tools, system_prompt):
    assert model == 'fake-llm'
    assert 'available tools' in system_prompt
    return FakeLangChainDecisionAgent(tools)


def build_agent(quantity_available, total_predicted_demand, has_open_po=False):
    service = FakeForecastingService()
    forecast_tool = FakeForecastTool(total_predicted_demand)
    agent = DecisionAgent(
        stock_tool=FakeStockTool(quantity_available),
        forecast_tool=forecast_tool,
        po_status_tool=FakePOStatusTool(
            has_open_po=has_open_po, open_po_id=456 if has_open_po else None
        ),
        forecasting_service=service,
        reasoner=FakeReasoner(),
        llm='fake-llm',
        agent_factory=fake_agent_factory,
    )
    return agent, service, forecast_tool


def test_decision_agent_flags_stockout_and_persists_reorder_flag():
    agent, service, forecast_tool = build_agent(quantity_available=45, total_predicted_demand=62)

    result = agent.run({'product_ids': [1]})

    decision = result['results'][0]
    assert result['flags_created'] == 1
    assert decision['sku_code'] == 'SKU-001'
    assert decision['reorder_required'] is True
    assert decision['reorder_flag_id'] == 77
    assert service.persisted[0]['quantity_available'] == 45
    assert service.persisted[0]['total_predicted_demand'] == 62
    assert service.persisted[0]['safety_stock'] == 10
    assert '45' in decision['reasoning']
    assert '62' in decision['reasoning']
    assert forecast_tool.calls[0]['forecast_days'] == 7


def test_decision_agent_does_not_flag_sufficient_stock():
    agent, service, _ = build_agent(quantity_available=90, total_predicted_demand=62)

    result = agent.run({'product_id': 1})

    decision = result['results'][0]
    assert result['flags_created'] == 0
    assert decision['reorder_required'] is False
    assert service.persisted == []


def test_decision_agent_requires_agent_collected_observations():
    class IncompleteAgent:
        def invoke(self, input, config=None):
            return {'messages': [SimpleNamespace(content='stopped early')]}

    agent = DecisionAgent(
        stock_tool=FakeStockTool(45),
        forecast_tool=FakeForecastTool(62),
        po_status_tool=FakePOStatusTool(),
        forecasting_service=FakeForecastingService(),
        reasoner=FakeReasoner(),
        llm='fake-llm',
        agent_factory=lambda **kwargs: IncompleteAgent(),
    )

    try:
        agent.run({'product_id': 1})
    except Exception as exc:
        assert 'required observations' in str(exc)
    else:
        raise AssertionError('Expected missing observations to fail the decision run.')


def test_decision_agent_suppresses_duplicate_when_open_po_exists():
    agent, service, _ = build_agent(
        quantity_available=45, total_predicted_demand=62, has_open_po=True
    )

    result = agent.run({'product_id': 1})

    decision = result['results'][0]
    assert result['flags_created'] == 0
    assert decision['formula_requires_reorder'] is True
    assert decision['has_open_po'] is True
    assert decision['open_po_id'] == 456
    assert decision['reorder_required'] is False
    assert service.persisted == []
