"""Tests for config/renderers.py — ResponseEnvelopeRenderer."""

from unittest.mock import MagicMock

from django.test import TestCase

from config.renderers import ResponseEnvelopeRenderer


class ResponseEnvelopeRendererTest(TestCase):
    def setUp(self):
        self.renderer = ResponseEnvelopeRenderer()

    def _ctx(self, data, status_code=200, envelope_exempt=False):
        response = MagicMock()
        response.status_code = status_code
        view = MagicMock(spec=[]) if not envelope_exempt else None
        if envelope_exempt:
            view = MagicMock()
            view.envelope_exempt = True
        request = MagicMock()
        request.query_params = {'page': 1, 'page_size': 20}
        return {
            'view': view,
            'response': response,
            'request': request,
        }

    def test_error_status_passthrough(self):
        ctx = self._ctx({'error': 'bad'}, status_code=400)
        result = self.renderer.render({'error': 'bad'}, renderer_context=ctx)
        self.assertIn(b'"error"', result)

    def test_envelope_exempt_passthrough(self):
        ctx = self._ctx({'status': 'success', 'data': {}}, envelope_exempt=True)
        result = self.renderer.render({'status': 'success', 'data': {}}, renderer_context=ctx)
        self.assertIn(b'"status"', result)

    def test_already_enveloped_passthrough(self):
        ctx = self._ctx({'status': 'success', 'data': {}})
        result = self.renderer.render({'status': 'success', 'data': {}}, renderer_context=ctx)
        self.assertIn(b'"status"', result)

    def test_paginated_results_wrapped(self):
        ctx = self._ctx({'count': 2, 'results': [{'id': 1}, {'id': 2}]})
        result = self.renderer.render(
            {'count': 2, 'results': [{'id': 1}, {'id': 2}]}, renderer_context=ctx
        )
        self.assertIn(b'"data"', result)
        self.assertIn(b'"meta"', result)

    def test_results_without_count_wrapped(self):
        ctx = self._ctx({'results': [{'id': 1}]})
        result = self.renderer.render({'results': [{'id': 1}]}, renderer_context=ctx)
        self.assertIn(b'"data"', result)

    def test_list_data_wrapped(self):
        ctx = self._ctx([{'id': 1}, {'id': 2}])
        result = self.renderer.render([{'id': 1}, {'id': 2}], renderer_context=ctx)
        self.assertIn(b'"data"', result)
        self.assertIn(b'"meta"', result)

    def test_plain_dict_wrapped(self):
        ctx = self._ctx({'key': 'value'})
        result = self.renderer.render({'key': 'value'}, renderer_context=ctx)
        self.assertIn(b'"status"', result)
        self.assertIn(b'"data"', result)

    def test_invalid_page_params_default(self):
        ctx = self._ctx({'count': 1, 'results': []})
        ctx['request'].query_params = {'page': 'abc', 'page_size': 'xyz'}
        result = self.renderer.render({'count': 1, 'results': []}, renderer_context=ctx)
        self.assertIn(b'"meta"', result)

    def test_no_renderer_context(self):
        result = self.renderer.render({'key': 'val'}, renderer_context=None)
        self.assertIn(b'"status"', result)
