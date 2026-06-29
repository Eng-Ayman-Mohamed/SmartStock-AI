from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.multimodal.whisper import SpeechTranscriber


class SpeechTranscriberTest(TestCase):
    @patch.dict('os.environ', {'GROQ_API_KEY': 'gsk-test'})
    @patch('ai.llm.provider_config.get_whisper_client')
    def test_transcribe_calls_whisper_api(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='hello world')

        transcriber = SpeechTranscriber()
        result = transcriber.transcribe(b'audio-data', filename='test.webm')

        self.assertEqual(result, 'hello world')
        mock_client.audio.transcriptions.create.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    @patch('ai.llm.provider_config.get_whisper_client')
    def test_missing_api_key_raises_value_error(self, mock_get_client):
        mock_get_client.side_effect = ValueError('GROQ_API_KEY not set')
        transcriber = SpeechTranscriber()
        with self.assertRaises(ValueError) as ctx:
            transcriber.transcribe(b'audio-data')
        self.assertIn('API_KEY', str(ctx.exception))

    @patch.dict('os.environ', {'GROQ_API_KEY': 'gsk-test'})
    @patch('ai.llm.provider_config.get_whisper_client')
    def test_transcribe_passes_filename(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='ok')

        transcriber = SpeechTranscriber()
        transcriber.transcribe(b'data', filename='my-audio.mp3')

        call_kwargs = mock_client.audio.transcriptions.create.call_args
        self.assertEqual(call_kwargs.kwargs['file'].name, 'my-audio.mp3')

    @patch.dict('os.environ', {'GROQ_API_KEY': 'gsk-test'})
    @patch('ai.llm.provider_config.get_whisper_client')
    def test_client_is_lazily_initialized(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = MagicMock(text='ok')

        transcriber = SpeechTranscriber()
        mock_get_client.assert_not_called()

        transcriber.transcribe(b'data')
        mock_get_client.assert_called_once()

    @patch.dict('os.environ', {'GROQ_API_KEY': 'gsk-test'})
    @patch('ai.llm.provider_config.get_whisper_client')
    def test_transcribe_api_error_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = RuntimeError('API down')

        transcriber = SpeechTranscriber()
        with self.assertRaises(RuntimeError):
            transcriber.transcribe(b'data')
