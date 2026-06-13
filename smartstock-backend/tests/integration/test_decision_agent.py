from datetime import timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from ai.agents.decision_agent import DecisionAgent
from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.inventory.models import SKU, Category, Product, StockLevel, Supplier


class FakeLangChainDecisionAgent:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    def invoke(self, input, config=None):
        product_id = int(
            input['messages'][0]['content']
            .split('product_id=')[1]
            .split('.')[0]
        )
        stock = self.tools['stock_level_read_tool'].invoke({'product_id': product_id})
        self.tools['forecast_read_tool'].invoke(
            {'product_id': product_id, 'forecast_days': stock['lead_time_days']}
        )
        self.tools['po_status_check_tool'].invoke({'product_id': product_id})
        return {'messages': [SimpleNamespace(content='done')]}


def fake_agent_factory(model, tools, system_prompt):
    return FakeLangChainDecisionAgent(tools)


class StaticReasoner:
    def generate(self, payload):
        return f'{payload["sku_code"]} requires reorder: {payload["reorder_required"]}'


class DecisionAgentIntegrationTests(TestCase):
    def test_agent_uses_langchain_tools_and_persists_reorder_flag(self):
        category = Category.objects.create(name='Decision')
        supplier = Supplier.objects.create(
            name='Decision Supplier',
            contact_email='decision@example.com',
            default_lead_time_days=3,
        )
        product = Product.objects.create(
            name='Decision Product',
            category=category,
            supplier=supplier,
            safety_stock=5,
            reorder_point=10,
        )
        sku = SKU.objects.create(product=product, code='DECISION-SKU-001')
        StockLevel.objects.create(
            sku=sku,
            quantity_on_hand=8,
            quantity_reserved=1,
            reorder_point=10,
        )
        today = timezone.localdate()
        for offset in range(3):
            ForecastResult.objects.create(
                sku=sku,
                forecast_date=today + timedelta(days=offset),
                predicted_quantity=4,
            )

        agent = DecisionAgent(
            llm='fake-llm',
            agent_factory=fake_agent_factory,
            reasoner=StaticReasoner(),
        )

        result = agent.run({'product_id': product.id})

        decision = result['results'][0]
        flag = ReorderFlag.objects.get(sku=sku)
        assert decision['reorder_required'] is True
        assert decision['quantity_available'] == 7
        assert decision['total_predicted_demand'] == 12
        assert decision['threshold'] == 17
        assert decision['reorder_flag_id'] == flag.id
