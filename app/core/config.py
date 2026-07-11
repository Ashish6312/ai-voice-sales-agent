"""
Application Configuration

Centralized configuration for the AI Voice Sales Agent.

Loads all environment variables from the .env file and exposes
them through a singleton Settings object.

Every service should import:

from app.core.config import settings
"""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """
    Global Application Settings.
    """

    # =====================================================
    # Application
    # =====================================================

    app_name: str = Field(
        default="AI Voice Sales Agent",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="1.0.0",
        alias="APP_VERSION",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    host: str = Field(
        default="127.0.0.1",
        alias="HOST",
    )

    port: int = Field(
        default=8000,
        alias="PORT",
    )

    # =====================================================
    # Gemini
    # =====================================================

    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
    )

    model_name: str = Field(
        default="gemini-2.5-flash",
        alias="MODEL_NAME",
    )

    # =====================================================
    # Groq
    # =====================================================

    groq_api_key: str = Field(
        default="",
        alias="GROQ_API_KEY",
    )

    # =====================================================
    # Whisper
    # =====================================================

    whisper_model: str = Field(
        default="base",
        alias="WHISPER_MODEL",
    )

    whisper_device: str = Field(
        default="cpu",
        alias="WHISPER_DEVICE",
    )

    whisper_compute_type: str = Field(
        default="int8",
        alias="WHISPER_COMPUTE_TYPE",
    )

    # =====================================================
    # TTS
    # =====================================================

    tts_provider: str = Field(
        default="elevenlabs",
        alias="TTS_PROVIDER",
    )

    # =====================================================
    # ElevenLabs
    # =====================================================

    elevenlabs_api_key: str = Field(
        default="",
        alias="ELEVENLABS_API_KEY",
    )

    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        alias="ELEVENLABS_VOICE_ID",
    )

    elevenlabs_model_id: str = Field(
        default="eleven_turbo_v2_5",
        alias="ELEVENLABS_MODEL_ID",
    )

    elevenlabs_output_format: str = Field(
        default="mp3_44100_128",
        alias="ELEVENLABS_OUTPUT_FORMAT",
    )

    # =====================================================
    # Twilio
    # =====================================================

    twilio_account_sid: str = Field(
        default="",
        alias="TWILIO_ACCOUNT_SID",
    )

    twilio_auth_token: str = Field(
        default="",
        alias="TWILIO_AUTH_TOKEN",
    )

    twilio_phone_number: str = Field(
        default="",
        alias="TWILIO_PHONE_NUMBER",
    )

    # =====================================================
    # Excel CRM
    # =====================================================

    excel_file: str = Field(
        default="data/Leads.xlsx",
        alias="EXCEL_FILE",
    )

    # =====================================================
    # Knowledge Base
    # =====================================================

    knowledge_file: str = Field(
        default="app/knowledge/knowledge.txt",
        alias="KNOWLEDGE_FILE",
    )

    faiss_index: str = Field(
        default="app/knowledge/faiss.index",
        alias="FAISS_INDEX",
    )

    metadata_file: str = Field(
        default="app/knowledge/metadata.pkl",
        alias="METADATA_FILE",
    )

    # =====================================================
    # Audio Directories
    # =====================================================

    input_audio_dir: str = Field(
        default="audio/input",
        alias="INPUT_AUDIO_DIR",
    )

    output_audio_dir: str = Field(
        default="audio/output",
        alias="OUTPUT_AUDIO_DIR",
    )

    # =====================================================
    # Logging
    # =====================================================

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"

    # =====================================================
    # Public URL
    # =====================================================

    public_base_url: str = Field(
        default="",
        alias="PUBLIC_BASE_URL",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a singleton Settings instance.
    """
    return Settings()


settings = get_settings()