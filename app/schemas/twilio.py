from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter(prefix="/twilio", tags=["Twilio"])


@router.post("/voice")
async def voice(request: Request):

    print("=" * 60)
    print("VOICE WEBHOOK HIT")
    print("=" * 60)

    form = await request.form()

    print(dict(form))

    response = VoiceResponse()

    response.say(
        "Hello. Twilio webhook is working.",
        voice="alice",
    )

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/status")
async def status(request: Request):

    print("=" * 60)
    print("STATUS WEBHOOK")
    print("=" * 60)

    form = await request.form()

    print(dict(form))

    return {"success": True}