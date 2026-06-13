from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.multimodal.whisper import SpeechTranscriber


class SpeechTranscriberTest(TestCase):
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_transcribe_calls_whisper_api(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='hello world')

        transcriber = SpeechTranscriber()
        result = transcriber.transcribe(b'audio-data', filename='test.webm')

        self.assertEqual(result, 'hello world')
        mock_client.audio.transcriptions.create.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_api_key_raises_value_error(self):
        transcriber = SpeechTranscriber()
        with self.assertRaises(ValueError) as ctx:
            transcriber.transcribe(b'audio-data')
        self.assertIn('OPENAI_API_KEY', str(ctx.exception))

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_transcribe_passes_filename(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='ok')

        transcriber = SpeechTranscriber()
        transcriber.transcribe(b'data', filename='my-audio.mp3')

        call_kwargs = mock_client.audio.transcriptions.create.call_args
        self.assertEqual(call_kwargs.kwargs['file'].name, 'my-audio.mp3')

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_client_is_lazily_initialized(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='ok')

        transcriber = SpeechTranscriber()
        mock_openai_cls.assert_not_called()

        transcriber.transcribe(b'data')
        mock_openai_cls.assert_called_once()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_transcribe_api_error_propagates(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = RuntimeError('API down')

        transcriber = SpeechTranscriber()
        with self.assertRaises(RuntimeError):
            transcriber.transcribe(b'data')
