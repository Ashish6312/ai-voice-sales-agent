"""
Speech-to-Text (STT) Service

This service handles the transcription of customer spoken audio using the 'Faster-Whisper' library.
Faster-Whisper is a high-performance reimplementation of OpenAI's Whisper model using CTranslate2,
making it up to 4x faster than the original PyTorch model while consuming significantly less CPU/GPU memory.

Key Configuration & Options:
----------------------------
1. Model Size (settings.whisper_model): Configured in settings (defaults to 'base').
2. Device (settings.whisper_device): CPU execution (optimized for standard hosting containers).
3. Compute Type (settings.whisper_compute_type): Defaults to 'int8' for quantized weights, 
   saving 50% of the RAM compared to float16 with negligible accuracy drop.

Execution parameters in transcribe():
-------------------------------------
- beam_size=5: Maintains the top 5 translation hypotheses at each step, balancing transcription speed and quality.
- vad_filter=True: Uses Silero VAD (Voice Activity Detection) to detect actual human speech and automatically ignore 
  background noises or long periods of silence before passing it to the Whisper model.
"""

from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings


class STTService:
    """
    Speech-to-Text Transcription Service using a local Faster-Whisper instance.
    """

    _shared_model = None

    def __init__(self):
        """
        Initialize Faster-Whisper model using application settings.
        """
        pass

    @property
    def model(self):
        """
        Lazily load the Whisper model on first request.
        """
        if STTService._shared_model is None:
            print("=" * 60)
            print("Loading Faster-Whisper Model...")
            print("=" * 60)

            STTService._shared_model = WhisperModel(
                model_size_or_path=settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )

            print(f"Model        : {settings.whisper_model}")
            print(f"Device       : {settings.whisper_device}")
            print(f"Compute Type : {settings.whisper_compute_type}")
            print("Whisper Model Loaded Successfully!")
        return STTService._shared_model

    # --------------------------------------------------
    # Speech To Text
    # --------------------------------------------------

    def transcribe(
        self,
        audio_path: str,
    ) -> str:
        """
        Convert speech into text.

        Parameters
        ----------
        audio_path : str
            Path to audio file.

        Returns
        -------
        str
            Complete transcript.
        """

        audio_file = Path(audio_path)

        if not audio_file.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        try:

            print("\n" + "=" * 60)
            print("Speech Recognition")
            print("=" * 60)

            print(f"Audio File : {audio_file}")

            segments, info = self.model.transcribe(
                str(audio_file),
                beam_size=5,
                vad_filter=True,
            )

            print(f"Language   : {info.language}")
            print(
                f"Confidence : "
                f"{info.language_probability:.2f}"
            )

            transcript = []

            print("\nSegments")
            print("-" * 60)

            for segment in segments:

                text = segment.text.strip()

                print(
                    f"[{segment.start:.2f}s - "
                    f"{segment.end:.2f}s]"
                )

                print(text)

                transcript.append(text)

            final_text = " ".join(transcript).strip()

            print("\n" + "=" * 60)
            print("Final Transcript")
            print("=" * 60)

            print(final_text)

            return final_text

        except Exception as e:

            raise RuntimeError(
                f"Speech recognition failed: {e}"
            ) from e