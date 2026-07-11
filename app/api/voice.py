"""
Voice API

Provides an endpoint to process customer voice input.

Flow:
Audio Upload
    ↓
Speech-to-Text
    ↓
AI Conversation
    ↓
Text-to-Speech
    ↓
Return Transcript + AI Response + Generated Audio
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


@router.post("/chat")
async def voice_chat(
    session_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a WAV file and receive an AI-generated voice response.
    """

    try:
        from app.services.voice.voice_service import VoiceService
        voice_service = VoiceService()

        os.makedirs("audio/input", exist_ok=True)
        os.makedirs("audio/output", exist_ok=True)

        input_path = os.path.join(
            "audio",
            "input",
            f"{uuid.uuid4()}.wav",
        )

        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = voice_service.process_audio(
            session_id=session_id,
            audio_path=input_path,
        )

        output_path = os.path.join(
            "audio",
            "output",
            f"{uuid.uuid4()}.mp3",
        )

        voice_service.save_audio(
            result["audio"],
            output_path,
        )

        return {
            "transcript": result["transcript"],
            "response": result["response"],
            "audio_file": output_path,
            "history": result["history"],
            "context": result["context"],
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Download generated audio.
    """

    file = Path("audio/output") / filename

    if not file.exists():

        raise HTTPException(

            status_code=404,

            detail="Audio file not found.",

        )

    return FileResponse(

        file,

        media_type="audio/mpeg",

    )


@router.get("/static/{filename}")
async def get_static_audio(filename: str):
    """
    Serve static audio files (e.g. hold music).
    """
    file = Path("audio/static") / filename
    if not file.exists():
        raise HTTPException(status_code=404, detail="Static audio file not found.")
    return FileResponse(file, media_type="audio/mpeg")