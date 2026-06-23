"""Tests for VisionExtractor PDF rasterization and OpenAI-compatible extraction."""

import base64
import json
import sys
import types

import pytest

from ai.multimodal.vision import VisionExtractor


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _RecordingClient:
    """Captures the messages passed to chat.completions.create."""

    def __init__(self, content):
        self._content = content
        self.captured = None
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.captured = kwargs
        return _FakeResponse(self._content)


class _FakePage:
    """Stand-in for a PIL image returned by pdf2image."""

    def convert(self, mode):
        return self

    def save(self, buffer, format, quality):  # noqa: A002 - mirrors PIL signature
        buffer.write(b'fake-jpeg-bytes')


def _data_url(mime, payload=b'data'):
    encoded = base64.b64encode(payload).decode('ascii')
    return f'data:{mime};base64,{encoded}'


def _extractor(client):
    extractor = VisionExtractor.__new__(VisionExtractor)
    extractor._provider = 'groq'
    extractor.client = client
    extractor.model = 'fake-vision-model'
    extractor.timeout = 15
    extractor._supports_vision = True
    return extractor


def _patch_pdf2image(monkeypatch, convert_fn):
    module = types.ModuleType('pdf2image')
    module.convert_from_bytes = convert_fn
    monkeypatch.setitem(sys.modules, 'pdf2image', module)


def test_is_pdf_detects_pdf_and_image():
    assert VisionExtractor._is_pdf(_data_url('application/pdf')) is True
    assert VisionExtractor._is_pdf(_data_url('image/png')) is False
    assert VisionExtractor._is_pdf(_data_url('image/jpeg')) is False


def test_image_is_passed_through_unchanged():
    client = _RecordingClient(json.dumps({'header': {}, 'line_items': []}))
    image_url = _data_url('image/png')

    result = _extractor(client)._extract_openai_compatible(image_url)

    assert result == {'header': {}, 'line_items': []}
    content = client.captured['messages'][1]['content']
    image_parts = [p for p in content if p['type'] == 'image_url']
    assert len(image_parts) == 1
    assert image_parts[0]['image_url']['url'] == image_url


def test_pdf_is_rasterized_to_jpeg_images(monkeypatch):
    _patch_pdf2image(monkeypatch, lambda *a, **k: [_FakePage(), _FakePage()])
    client = _RecordingClient(json.dumps({'header': {}, 'line_items': []}))

    _extractor(client)._extract_openai_compatible(_data_url('application/pdf'))

    content = client.captured['messages'][1]['content']
    image_parts = [p for p in content if p['type'] == 'image_url']
    assert len(image_parts) == 2
    for part in image_parts:
        assert part['image_url']['url'].startswith('data:image/jpeg;base64,')


def test_pdf_page_cap_is_passed_to_converter(monkeypatch):
    captured = {}

    def fake_convert(pdf_bytes, **kwargs):
        captured.update(kwargs)
        return [_FakePage()]

    _patch_pdf2image(monkeypatch, fake_convert)
    client = _RecordingClient(json.dumps({'header': {}, 'line_items': []}))

    _extractor(client)._extract_openai_compatible(_data_url('application/pdf'))

    assert captured['last_page'] == VisionExtractor.MAX_PDF_PAGES
    assert captured['dpi'] == VisionExtractor.PDF_DPI


def test_corrupt_pdf_raises_value_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError('broken pdf')

    _patch_pdf2image(monkeypatch, boom)

    with pytest.raises(ValueError, match='Could not read PDF invoice'):
        _extractor(_RecordingClient(''))._convert_pdf_to_images(_data_url('application/pdf'))


def test_pdf_with_no_pages_raises_value_error(monkeypatch):
    _patch_pdf2image(monkeypatch, lambda *a, **k: [])

    with pytest.raises(ValueError, match='no readable pages'):
        _extractor(_RecordingClient(''))._convert_pdf_to_images(_data_url('application/pdf'))


def test_missing_pdf2image_raises_value_error(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pdf2image', None)

    with pytest.raises(ValueError, match='requires the pdf2image package'):
        _extractor(_RecordingClient(''))._convert_pdf_to_images(_data_url('application/pdf'))
