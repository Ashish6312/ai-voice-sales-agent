"""
Voice API

Upload audio
↓

Speech-to-Text

↓

Conversation

↓

Text-to-Speech
"""

import os
import uuid

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from fastapi.responses import JSONResponse

from app.services.voice.voice_service import VoiceService

router = APIRouter(

    prefix="/voice",

    tags=["Voice"],
)

voice = VoiceService()


@router.post("/chat")
async def voice_chat(

    session_id: str,

    file: UploadFile = File(...),
):

    try:

        os.makedirs(
            "audio/input",
            exist_ok=True,
        )

        filename = f"{uuid.uuid4()}.wav"

        input_path = os.path.join(
            "audio/input",
            filename,
        )

        with open(
            input_path,
            "wb",
        ) as f:

            f.write(await file.read())

        result = voice.process_audio(

            session_id=session_id,

            audio_path=input_path,
        )

        output_path = os.path.join(

            "audio/output",

            f"{uuid.uuid4()}.mp3",
        )

        voice.save_audio(

            result["audio"],

            output_path,
        )

        return JSONResponse(

            {

                "transcript": result["transcript"],

                "response": result["response"],

                "audio_file": output_path,
            }

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e),
        )