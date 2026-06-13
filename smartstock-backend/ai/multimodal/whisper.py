import io
import logging
import os

logger = logging.getLogger(__name__)


class SpeechTranscriber:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError('OPENAI_API_KEY is missing.')
            self._client = OpenAI(api_key=api_key)
        return self._client

    def transcribe(self, audio_data: bytes, filename: str = 'audio.webm') -> str:
        client = self._get_client()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename
        response = client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
        )
        return response.text
