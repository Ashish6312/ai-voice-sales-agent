"""
Voice Service

Complete Voice Pipeline

Audio
   ↓
STT
   ↓
Sales Agent
   ↓
CRM Update
   ↓
TTS
"""

import logging
import threading
import time
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)

from app.services.stt_service import STTService
from app.services.sales_agent import SalesAgent
from app.services.crm_service import CRMService
from app.services.session_manager import SessionManager
from app.services.voice.tts_factory import TTSFactory


class VoiceService:

    def __init__(self):

        self.stt = STTService()

        self.sales_agent = SalesAgent()

        self.crm = CRMService()

        self.sessions = SessionManager()

        self.tts = TTSFactory.create()

    # ----------------------------------------------------

    def process_audio(
        self,
        session_id: str,
        audio_path: str = None,
        transcript: str = None,
    ) -> dict:

        # ------------------------------------
        # STT
        # ------------------------------------

        if audio_path:

            transcript = self.stt.transcribe(
                audio_path
            )

        # ------------------------------------
        # SALES AGENT
        # ------------------------------------

        result = self.sales_agent.process(

            session_id=session_id,

            customer_message=transcript,

        )

        session = self.sessions.get_session(
            session_id
        )

        # ------------------------------------
        # UPDATE CRM
        # ------------------------------------

        if session["lead_id"] is not None:

            self.crm.upsert_lead(

                lead_id=session["lead_id"],

                crm_update=result["crm_update"],

            )

        # ------------------------------------
        # TTS
        # ------------------------------------

        audio_bytes = self.tts.synthesize(

            result["reply"]

        )

        # Clean up old audio files asynchronously to avoid request latency
        threading.Thread(
            target=self._cleanup_old_audio,
            daemon=True,
        ).start()

        # Save reply audio to dynamic UUID-based filename: reply_<session_id>_<uuid4_hex>.mp3 for Twilio
        filename = f"reply_{session_id}_{uuid4().hex}.mp3"
        output_path = Path("audio/output") / filename
        self.save_audio(audio_bytes, str(output_path))

        # Update Session fields
        session["last_audio"] = filename
        session["crm"] = result["crm_update"]

        return {

            "audio_file": filename,

            "audio": audio_bytes,

            "end_call": result["end_call"],

            "crm": result["crm_update"],

            "intent": result["intent"],

            "reply": result["reply"],

            "transcript": transcript,

        }

    # ----------------------------------------------------

    def save_audio(

        self,

        audio: bytes,

        output_path: str,

    ) -> str:

        output = Path(output_path)

        output.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        output.write_bytes(audio)

        return str(output)

    def _cleanup_old_audio(self):

        output_dir = Path("audio/output")

        if not output_dir.exists():
            return

        now = time.time()

        for file in output_dir.glob("*.mp3"):

            try:

                age = now - file.stat().st_mtime

                if age > 300:

                    logger.info(
                        f"Deleting old audio {file.name}"
                    )

                    file.unlink()

            except Exception as e:

                logger.warning(e)