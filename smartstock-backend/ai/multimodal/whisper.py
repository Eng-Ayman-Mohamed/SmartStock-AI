import io
import logging

logger = logging.getLogger(__name__)


class SpeechTranscriber:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from ai.llm.provider_config import PROVIDER, get_whisper_client

            self._client = get_whisper_client()
            self._provider = PROVIDER
        return self._client

    def transcribe(self, audio_data: bytes, filename: str = 'audio.webm') -> str:
        from ai.llm.provider_config import get_provider_config

        client = self._get_client()
        config = get_provider_config()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        if self._provider == 'groq':
            response = client.audio.transcriptions.create(
                model=config['whisper_model'],
                file=audio_file,
            )
        else:
            response = client.audio.transcriptions.create(
                model=config['whisper_model'],
                file=audio_file,
            )
        return response.text
