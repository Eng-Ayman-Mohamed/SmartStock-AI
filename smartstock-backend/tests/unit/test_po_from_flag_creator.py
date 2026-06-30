"""Tests for POFromFlagCreator."""

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.agents.po_from_flag_creator import POFromFlagCreator


class _FakeFlag:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.sku_id = kwargs.get('sku_id', 100)
        self.quantity_available = kwargs.get('quantity_available', 10)
        self.total_predicted_demand = kwargs.get('total_predicted_demand', 50.0)
        self.safety_stock = kwargs.get('safety_stock', 5)
        self.lead_time_days = kwargs.get('lead_time_days', 7)
        self.forecast_days = kwargs.get('forecast_days', 30)
        self.reasoning = kwargs.get('reasoning', 'Stock below reorder point')
        self.status = kwargs.get('status', 'OPEN')
        self.reorder_required = kwargs.get('reorder_required', True)
        self.has_open_po = kwargs.get('has_open_po', False)

    class Status:
        OPEN = 'OPEN'
        CONSUMED = 'CONSUMED'

    def save(self, update_fields=None):
        pass


class _FakeProduct:
    def __init__(self):
        self.unit_price = Decimal('25.00')
        self.supplier = _FakeSupplier()


class _FakeSupplier:
    def __init__(self):
        self.id = 1
        self.name = 'Test Supplier'
        self.default_lead_time_days = 14
        self.contact_email = 'supplier@test.com'


class _FakeSKU:
    def __init__(self):
        self.id = 100
        self.code = 'SKU-TEST-001'
        self.product = _FakeProduct()


def _make_mock_chain(result_str):
    mock_prompt_instance = MagicMock()
    mock_step1 = MagicMock()
    mock_step2 = MagicMock()
    mock_step2.invoke.return_value = result_str
    mock_prompt_instance.__or__.return_value = mock_step1
    mock_step1.__or__.return_value = mock_step2
    return mock_prompt_instance, mock_step2


class POFromFlagCreatorProcessFlagsTest(TestCase):
    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_created(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        mock_llm = MagicMock()
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'pending_approval', 'po_id': 42}

        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 100, 'reasoning': 'Low stock'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock

        creator = POFromFlagCreator(llm=mock_llm, purchasing_agent=mock_agent)
        results = creator.process_flags([_FakeFlag()])
        self.assertEqual(results['created'], 1)

    @patch('ai.agents.po_from_flag_creator.SKU')
    def test_skipped_no_supplier(self, mock_sku_cls):
        flag = _FakeFlag()
        sku = _FakeSKU()
        sku.product.supplier = None
        mock_sku_cls.objects.select_related.return_value.get.return_value = sku
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        results = creator.process_flags([flag])
        self.assertEqual(results['skipped_no_supplier'], 1)

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_failed_invalid_json(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        prompt_mock, chain_mock = _make_mock_chain('not valid json')
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        results = creator.process_flags([_FakeFlag()])
        self.assertEqual(results['failed'], 1)

    @patch('ai.agents.po_from_flag_creator.SKU')
    def test_exception_in_process_single_flag(self, mock_sku_cls):
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        with patch.object(creator, '_process_single_flag', side_effect=RuntimeError('boom')):
            results = creator.process_flags([_FakeFlag()])
        self.assertEqual(results['failed'], 1)
        self.assertIn('boom', results['errors'])

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_multiple_flags(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'pending_approval', 'po_id': 1}
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 50, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        results = creator.process_flags([_FakeFlag(id=1), _FakeFlag(id=2), _FakeFlag(id=3)])
        self.assertEqual(results['created'], 3)

    def test_empty_flags(self):
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        results = creator.process_flags([])
        self.assertEqual(results['created'], 0)


class POFromFlagCreatorProcessSingleFlagTest(TestCase):
    @patch('ai.agents.po_from_flag_creator.SKU')
    def test_no_supplier_skips(self, mock_sku_cls):
        sku = _FakeSKU()
        sku.product.supplier = None
        mock_sku_cls.objects.select_related.return_value.get.return_value = sku
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'skipped_no_supplier')

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_invalid_json_from_llm(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        prompt_mock, chain_mock = _make_mock_chain('not valid json')
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('invalid JSON', result['error'])

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_llm_missing_fields(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        prompt_mock, chain_mock = _make_mock_chain(json.dumps({'supplier_id': 1}))
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=MagicMock())
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('missing supplier_id or quantity', result['error'])

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_purchasing_agent_failure(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'failed', 'error': 'email failed'}
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 50, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('email failed', result['error'])

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_total_cost_with_unit_price(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        sku = _FakeSKU()
        sku.product.unit_price = Decimal('10.00')
        mock_sku_cls.objects.select_related.return_value.get.return_value = sku
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'pending_approval', 'po_id': 1}
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 20, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'created')
        call_args = mock_agent.run.call_args[0][0]
        self.assertEqual(call_args['total_cost'], '200.00')

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_total_cost_with_none_unit_price(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        sku = _FakeSKU()
        sku.product.unit_price = None
        mock_sku_cls.objects.select_related.return_value.get.return_value = sku
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'pending_approval', 'po_id': 1}
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 20, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'created')
        call_args = mock_agent.run.call_args[0][0]
        self.assertEqual(call_args['total_cost'], '0.00')

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_supplier_without_email(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        sku = _FakeSKU()
        sku.product.supplier.contact_email = None
        mock_sku_cls.objects.select_related.return_value.get.return_value = sku
        mock_agent = MagicMock()
        mock_agent.run.return_value = {'status': 'pending_approval', 'po_id': 1}
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 20, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'created')

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_integrity_error(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        from django.db import IntegrityError

        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        mock_agent = MagicMock()
        mock_agent.run.side_effect = IntegrityError('duplicate')
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 20, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('duplicate PO', result['error'])

    @patch('ai.agents.po_from_flag_creator.SKU')
    @patch('ai.agents.po_from_flag_creator.StrOutputParser')
    @patch('ai.agents.po_from_flag_creator.ChatPromptTemplate')
    def test_unexpected_error(self, mock_prompt_cls, mock_parser_cls, mock_sku_cls):
        mock_sku_cls.objects.select_related.return_value.get.return_value = _FakeSKU()
        mock_agent = MagicMock()
        mock_agent.run.side_effect = RuntimeError('unexpected')
        prompt_mock, chain_mock = _make_mock_chain(
            json.dumps({'supplier_id': 1, 'quantity': 20, 'reasoning': 'test'})
        )
        mock_prompt_cls.from_messages.return_value = prompt_mock
        creator = POFromFlagCreator(llm=MagicMock(), purchasing_agent=mock_agent)
        result = creator._process_single_flag(_FakeFlag())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('unexpected error', result['error'])
