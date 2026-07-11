"""
Production Text-to-Speech Service

Uses ElevenLabs to generate human-like speech.
"""

from pathlib import Path

from elevenlabs.client import ElevenLabs

from app.core.config import settings


class TTSService:
    """
    Enterprise Text-to-Speech Service.
    """

    def __init__(self):

        self.client = ElevenLabs(
            api_key=settings.elevenlabs_api_key
        )

        self.voice_id = settings.elevenlabs_voice_id

        self.model_id = settings.elevenlabs_model_id

        self.output_dir = Path("audio/output")

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # --------------------------------------------------

    def synthesize(
        self,
        text: str,
        filename: str = "reply.mp3",
    ) -> str:
        """
        Convert text into speech.

        Returns
        -------
        str
            Path to generated audio.
        """

        output_path = self.output_dir / filename

        audio = self.client.text_to_speech.convert(

            voice_id=self.voice_id,

            model_id=self.model_id,

            text=text,

            output_format="mp3_44100_128",
        )

        with open(output_path, "wb") as f:

            for chunk in audio:

                if chunk:

                    f.write(chunk)

        return str(output_path)

    # --------------------------------------------------

    def available_voice(self):

        return self.voice_id