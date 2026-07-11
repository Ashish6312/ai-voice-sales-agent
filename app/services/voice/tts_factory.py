"""
TTS Factory

Creates the configured Text-to-Speech provider.

The rest of the application should never instantiate
a concrete TTS provider directly.

Instead use:

tts = TTSFactory.create()
"""

from app.core.config import settings

from app.services.voice.base_tts import BaseTTS
from app.services.voice.elevenlabs_tts import ElevenLabsTTS


class TTSFactory:

    _provider = None

    @classmethod
    def create(cls) -> BaseTTS:

        if cls._provider is not None:
            return cls._provider

        provider = settings.tts_provider.lower()

        if provider == "elevenlabs":
            cls._provider = ElevenLabsTTS()
            return cls._provider

        raise ValueError(
            f"Unsupported TTS provider: {provider}"
        )