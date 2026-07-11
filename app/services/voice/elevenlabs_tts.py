"""
ElevenLabs Text-to-Speech Provider
"""

import time

from elevenlabs import ElevenLabs

from app.core.config import settings
from app.services.voice.base_tts import BaseTTS


class ElevenLabsTTS(BaseTTS):

    def __init__(self):

        self.client = ElevenLabs(
            api_key=settings.elevenlabs_api_key,
        )

    def synthesize(
        self,
        text: str,
    ) -> bytes:

        last_exception = None

        for attempt in range(3):

            try:

                print("\nGenerating Speech...")

                audio = self.client.text_to_speech.convert(

                    voice_id=settings.elevenlabs_voice_id,

                    model_id=settings.elevenlabs_model_id,

                    text=text,

                    output_format=settings.elevenlabs_output_format,

                    optimize_streaming_latency="3",
                )

                result = bytearray()

                for chunk in audio:

                    if chunk:

                        result.extend(chunk)

                print("Speech Generated Successfully!")

                return bytes(result)

            except Exception as e:

                last_exception = e

                print(f"TTS Retry {attempt+1}/3")

                time.sleep(2)

        raise RuntimeError(last_exception)