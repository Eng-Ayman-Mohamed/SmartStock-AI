from django.conf import settings
from pathlib import Path


class FileStorage:
    def __init__(self):
        self.base_path = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path('/tmp/uploads')

    def save(self, name: str, content: bytes) -> str:
        filepath = self.base_path / name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(content)
        return str(filepath)
