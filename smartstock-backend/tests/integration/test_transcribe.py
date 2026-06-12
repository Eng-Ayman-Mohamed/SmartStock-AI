from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser


class TranscribeEndpointTests(APITestCase):
    """Integration tests for POST /api/ai/transcribe/"""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='StrongPass123!',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _url(self):
        return '/api/ai/transcribe/'

    def _auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def _audio_file(self, name='test.webm', content=b'fake-audio-data'):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(name, content, content_type='audio/webm')

    # --- Authentication & RBAC ---

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_unauthenticated_returns_401(self, mock_transcribe):
        response = self.client.post(self._url(), {'audio': self._audio_file()})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_transcribe.assert_not_called()

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_viewer_returns_403(self, mock_transcribe):
        self._auth(self.viewer)
        response = self.client.post(self._url(), {'audio': self._audio_file()})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_transcribe.assert_not_called()

    # --- Success ---

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_transcribe_returns_200_with_text(self, mock_transcribe):
        mock_transcribe.return_value = 'hello from whisper'
        self._auth(self.manager)
        response = self.client.post(self._url(), {'audio': self._audio_file()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['text'], 'hello from whisper')
        mock_transcribe.assert_called_once()

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_transcribe_passes_filename_to_whisper(self, mock_transcribe):
        mock_transcribe.return_value = 'ok'
        self._auth(self.manager)
        response = self.client.post(self._url(), {'audio': self._audio_file(name='my-clip.mp3')})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_args = mock_transcribe.call_args
        self.assertEqual(call_args.kwargs['filename'], 'my-clip.mp3')

    # --- Error handling ---

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_whisper_failure_returns_500(self, mock_transcribe):
        mock_transcribe.side_effect = RuntimeError('Whisper API error')
        self._auth(self.manager)
        response = self.client.post(self._url(), {'audio': self._audio_file()})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status'], 'error')

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_missing_api_key_returns_500(self, mock_transcribe):
        mock_transcribe.side_effect = ValueError('OPENAI_API_KEY is missing.')
        self._auth(self.manager)
        response = self.client.post(self._url(), {'audio': self._audio_file()})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_missing_audio_returns_400(self):
        self._auth(self.manager)
        response = self.client.post(self._url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('ai.multimodal.whisper.SpeechTranscriber.transcribe')
    def test_file_too_large_returns_400(self, mock_transcribe):
        from django.core.files.uploadedfile import SimpleUploadedFile

        large_file = SimpleUploadedFile(
            'big.webm', b'x' * (25 * 1024 * 1024 + 1), content_type='audio/webm'
        )
        self._auth(self.manager)
        response = self.client.post(self._url(), {'audio': large_file})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_transcribe.assert_not_called()
