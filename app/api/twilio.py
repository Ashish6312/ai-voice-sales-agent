"""
Twilio API

Handles Twilio call loop webhooks, processing customer speech transcripts,
updating CRM databases, and returning voice responses.
"""

from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.core.config import settings
from app.services.session_manager import SessionManager
from app.services.excel_service import ExcelService
from app.services.voice.voice_service import VoiceService

# Initialize the heavy AI models globally on startup!
voice_service = VoiceService()

router = APIRouter(
    prefix="/twilio",
    tags=["Twilio"],
)


def find_session_by_phone(phone: str) -> str | None:
    """
    Finds an active, non-ended session matching the last 10 digits of the phone number.
    """
    if not phone:
        return None

    session_manager = SessionManager()
    cleaned_target = "".join(c for c in phone if c.isdigit())
    if len(cleaned_target) > 10:
        cleaned_target = cleaned_target[-10:]

    for session in session_manager.list_sessions():
        if not session["phone"] or session["ended"]:
            continue
        # Skip sessions that don't have a valid lead_id
        if not session.get("lead_id"):
            continue

        cleaned_session_phone = "".join(
            c for c in session["phone"] if c.isdigit()
        )
        if len(cleaned_session_phone) > 10:
            cleaned_session_phone = cleaned_session_phone[-10:]

        if cleaned_session_phone == cleaned_target:
            return session["session_id"]

    return None


@router.post("/voice")
async def voice(
    request: Request,
    To: str = Form(None),
    From: str = Form(None),
    CallSid: str = Form(None),
    session_id: str = None,
    retry: str = None,
):
    """
    Called when a customer answers or joins a call.
    Greet the customer and start gathering speech input.
    """
    print(f"Voice webhook received: To={To}, From={From}, CallSid={CallSid}")
    
    session_manager = SessionManager()

    # Determine customer phone number (To for outbound calls, From for inbound calls)
    customer_phone = To or ""
    if customer_phone == settings.twilio_phone_number:
        customer_phone = From or ""

    phone = customer_phone
    session_id = session_id or find_session_by_phone(phone)
    
    print(f"Phone lookup: phone={phone}, session_id={session_id}")

    if not session_id:
        session_id = session_manager.create_session(phone=phone)
        print(f"Created new session: {session_id}")

    # Sync Call SID to Excel CRM for the correct lead row
    if CallSid:
        try:
            session = session_manager.get_session(session_id)
            lead_id = session.get("lead_id")
            excel_service = ExcelService()
            lead_row = None

            if lead_id is not None:
                # Find row by Lead ID (accurate even when multiple leads share the same phone)
                lead_id_col = excel_service.headers.get("Lead ID")
                if lead_id_col:
                    for r in range(2, excel_service.sheet.max_row + 1):
                        cell_val = excel_service.sheet.cell(row=r, column=lead_id_col).value
                        if cell_val is not None and int(cell_val) == int(lead_id):
                            lead_row = r
                            break

            if lead_row:
                excel_service.update_lead_by_row(lead_row, {
                    "Last Call SID": CallSid,
                    "Call Status": "Ringing"
                })
            excel_service.close()
            print(f"Updated Excel with CallSid, lead_id={lead_id}, lead_row={lead_row}")
        except Exception as e:
            print(f"Failed to update lead Last Call SID in voice webhook: {e}")

    response = VoiceResponse()
    session = session_manager.get_session(session_id)
    gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"

    # Twilio <Gather> to capture the greeting response with stable auto-timeout
    # Accept both Hindi and English from the very first turn
    gather = response.gather(
        input="speech",
        speechTimeout="auto",
        timeout=7,
        language=gather_lang,
        hints="हाँ,नहीं,हेलो,pricing,demo,meeting,interested,manual,busy",
        action=f"/twilio/process?session_id={session_id}",
        method="POST",
    )

    # Check if this is a retry attempt from silence
    is_retry = retry == "true" or request.query_params.get("retry") == "true"

    customer_name = ""
    if not is_retry:
        try:
            from app.services.crm_service import CRMService
            crm = CRMService()
            lead_id = session.get("lead_id")
            if lead_id:
                lead = crm.get_lead(int(lead_id))
                if lead and lead.get("Name"):
                    name_val = str(lead.get("Name")).strip()
                    # Skip generic placeholder names like 'Lead X'
                    if name_val and not name_val.lower().startswith("lead"):
                        customer_name = name_val
        except Exception as ce:
            print(f"Failed to fetch customer name for personalized greeting: {ce}")

    if is_retry:
        if session.get("language") == "hi":
            gather.say(
                "माफ़ कीजिए, मैं सुन नहीं पाया। क्या आप दोबारा बोल सकते हैं?",
                voice="alice",
                language="hi-IN",
            )
        else:
            gather.say(
                "Sorry, I didn't catch that. Could you please repeat?",
                voice="alice",
                language="en-US",
            )
    else:
        # Personalized greeting if name is available, otherwise default greeting
        if customer_name:
            greeting_text = f"Hello {customer_name}, this is Ashish from AI Solutions. How can I help you today?"
        else:
            greeting_text = "Hello, this is Ashish from AI Solutions. How can I help you today?"

        gather.say(
            greeting_text,
            voice="alice",
            language="en-US",
        )

    # Fallback response: if gather times out with silence, loop back with retry query
    response.redirect(f"/twilio/voice?session_id={session_id}&retry=true")

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/process")
async def process(
    request: Request,
    session_id: str = None,
    SpeechResult: str = Form(None),
    Digits: str = Form(None),
):
    """
    Processes transcribed speech from the gather verb.
    Starts AI processing in a background thread, returns hold tune immediately,
    then /twilio/wait picks up the result when ready.
    """
    import threading

    response = VoiceResponse()

    # Fallback to query parameters if session_id is not bound directly
    if not session_id:
        session_id = request.query_params.get("session_id")

    if not session_id:
        response.say("Error: session ID not found.", voice="alice")
        response.hangup()
        return Response(
            content=str(response),
            media_type="application/xml",
        )

    # Handle keypad digit(s) gracefully without calling Gemini
    if Digits:
        print(f"User pressed keypad digit(s): {Digits}")
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)
        gather_lang = "en-IN"
        if session:
            gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"

        response.say(
            "Please speak your response instead of using the keypad.",
            voice="alice",
            language="en-US"
        )
        response.gather(
            input="speech",
            speechTimeout="1",
            language=gather_lang,
            action=f"/twilio/process?session_id={session_id}",
            method="POST",
        )
        return Response(
            content=str(response),
            media_type="application/xml",
        )

    transcript = SpeechResult or ""
    print(f"[PROCESS] Received speech: '{transcript}' for session {session_id}")

    # Get public base URL for hold music
    public_base_url = settings.public_base_url
    if not public_base_url:
        public_base_url = str(request.base_url).rstrip("/")

    # Mark session as processing and start background thread
    session_manager = SessionManager()
    session = session_manager.get_session(session_id)
    session["ai_result"] = None
    session["ai_error"] = None
    session["ai_processing"] = True
    session["public_base_url"] = public_base_url

    def background_process():
        try:
            result = voice_service.process_audio(
                session_id=session_id,
                audio_path=None,
                transcript=transcript,
            )
            session["ai_result"] = result
            print(f"[PROCESS] Background AI completed for session {session_id}")
        except Exception as e:
            session["ai_error"] = str(e)
            print(f"[PROCESS] Background AI error: {e}")
        session["ai_processing"] = False

    thread = threading.Thread(target=background_process, daemon=True)
    thread.start()

    # Hybrid Sync/Async wait: Wait up to 2.5 seconds to see if AI responds quickly
    import time
    waited = 0.0
    while waited < 2.5:
        if not session.get("ai_processing"):
            break
        time.sleep(0.1)
        waited += 0.1

    # Check if result is already ready (fast response case)
    if session.get("ai_result"):
        result = session["ai_result"]
        session["ai_result"] = None  # Clear

        # Detect Hindi
        is_hindi = any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in result["reply"])
        session["language"] = "hi" if is_hindi else "en"

        audio_url = f"{public_base_url}/voice/audio/{result['audio_file']}"

        if result["end_call"]:
            response.play(audio_url)
            response.hangup()
        else:
            response.play(audio_url)
            gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"
            response.gather(
                input="speech",
                speechTimeout="auto",
                timeout=7,
                language=gather_lang,
                hints="\u0939\u093e\u0901,\u0928\u0939\u0940\u0902,\u0939\u0947\u0932\u094b,pricing,demo,meeting,interested,manual,busy",
                action=f"/twilio/process?session_id={session_id}",
                method="POST",
            )
            response.redirect(f"/twilio/voice?session_id={session_id}&retry=true")

        return Response(
            content=str(response),
            media_type="application/xml",
        )

    elif session.get("ai_error"):
        error_str = session["ai_error"]
        session["ai_error"] = None

        if "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            session["on_hold"] = True
            response.say(
                "Please hold on for a moment. Our executive is checking the details for you.",
                voice="alice",
                language="en-US",
            )
            response.pause(length=45)
            response.redirect(
                f"/twilio/resume?session_id={session_id}",
                method="POST",
            )
        else:
            response.say(
                "Thank you for your time. Our team will follow up with you shortly. Goodbye.",
                voice="alice",
            )
            response.hangup()

        return Response(
            content=str(response),
            media_type="application/xml",
        )

    # Slow response case: play ONLY the hold chime (no spoken speech) and redirect to background polling loop
    hold_url = f"{public_base_url}/voice/static/hold_tone.mp3"
    response.play(hold_url)
    response.redirect(
        f"/twilio/wait?session_id={session_id}",
        method="POST",
    )

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/wait")
async def wait_for_response(
    request: Request,
    session_id: str = None,
):
    """
    Polls for the background AI result.
    If ready, plays the response and gathers next turn.
    If not ready, plays more hold music and loops.
    """
    if not session_id:
        session_id = request.query_params.get("session_id")

    response = VoiceResponse()
    session_manager = SessionManager()

    try:
        session = session_manager.get_session(session_id)
    except Exception:
        response.say("Thank you for your time. Goodbye.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    public_base_url = session.get("public_base_url") or settings.public_base_url
    if not public_base_url:
        public_base_url = str(request.base_url).rstrip("/")

    # Check if AI result is ready
    if session.get("ai_result"):
        result = session["ai_result"]
        session["ai_result"] = None  # Clear

        # Detect Hindi
        is_hindi = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in result["reply"])
        session["language"] = "hi" if is_hindi else "en"

        audio_url = f"{public_base_url}/voice/audio/{result['audio_file']}"

        if result["end_call"]:
            response.play(audio_url)
            response.hangup()
        else:
            response.play(audio_url)
            gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"
            response.gather(
                input="speech",
                speechTimeout="auto",
                timeout=7,
                language=gather_lang,
                hints="\u0939\u093e\u0901,\u0928\u0939\u0940\u0902,\u0939\u0947\u0932\u094b,pricing,demo,meeting,interested,manual,busy",
                action=f"/twilio/process?session_id={session_id}",
                method="POST",
            )
            # Fallback if no speech
            response.redirect(f"/twilio/voice?session_id={session_id}&retry=true")

    elif session.get("ai_error"):
        error_str = session["ai_error"]
        session["ai_error"] = None

        if "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            # Quota hit — save transcript and hold
            session["on_hold"] = True
            response.say(
                "Please hold on for a moment. Our executive is checking the details for you.",
                voice="alice",
                language="en-US",
            )
            response.pause(length=45)
            response.redirect(
                f"/twilio/resume?session_id={session_id}",
                method="POST",
            )
        else:
            response.say(
                "Thank you for your time. Our team will follow up with you shortly. Goodbye.",
                voice="alice",
            )
            response.hangup()
    else:
        # Still processing — play hold tune and loop
        hold_url = f"{public_base_url}/voice/static/hold_tone.mp3"
        response.play(hold_url)
        response.redirect(
            f"/twilio/wait?session_id={session_id}",
            method="POST",
        )

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/status")
async def status(
    CallSid: str = Form(None),
    CallStatus: str = Form(None),
    To: str = Form(None),
    From: str = Form(None),
):
    """
    Webhook to receive call status updates from Twilio.
    """
    print("=" * 60)
    print("CALL STATUS UPDATE")
    print("=" * 60)
    print(f"Call SID : {CallSid}")
    print(f"Status   : {CallStatus}")
    print(f"To       : {To}")
    print(f"From     : {From}")

    if CallSid:
        try:
            excel_service = ExcelService()
            row = excel_service.find_row_by_call_sid(CallSid)

            # If Call SID is not found in sheet, do not fall back to phone
            # mapping because multiple leads share the same phone number.

            if row:
                lead = excel_service.get_lead_by_row(row)
                current_retry = lead.get("Retry Count")
                try:
                    current_retry = int(current_retry) if current_retry is not None else 0
                except (ValueError, TypeError):
                    current_retry = 0

                status_map = {
                    "queued": "Queued",
                    "ringing": "Ringing",
                    "in-progress": "Connected",
                    "completed": "Completed",
                    "busy": "Busy",
                    "no-answer": "No Answer",
                    "failed": "Failed",
                    "canceled": "Canceled"
                }
                mapped_status = status_map.get(CallStatus, CallStatus)

                updates = {
                    "Call Status": mapped_status
                }

                if CallStatus in ["busy", "no-answer", "failed"]:
                    updates["Retry Count"] = current_retry + 1
                elif CallStatus == "completed":
                    updates["Retry Count"] = 0

                excel_service.update_lead_by_row(row, updates)
                print(f"Updated Lead at row {row}: {updates}")

                # Trigger final conversation summarization if call completed successfully
                if CallStatus == "completed":
                    try:
                        lead_id_val = lead.get("Lead ID")
                        if lead_id_val:
                            session_manager = SessionManager()
                            session_id = None
                            for s in session_manager.list_sessions():
                                if str(s.get("lead_id")) == str(lead_id_val) and not s.get("ended"):
                                    session_id = s.get("session_id")
                                    break
                            if session_id:
                                print(f"Triggering final summarization for session {session_id}, lead {lead_id_val}")
                                from app.services.conversation_service import ConversationService
                                conversation_service = ConversationService()
                                conversation_service.end_conversation(session_id=session_id, lead_id=int(lead_id_val))
                                # Mark session as ended
                                session = session_manager.get_session(session_id)
                                session["ended"] = True
                            else:
                                print("No active session found to summarize.")
                    except Exception as se:
                        print(f"Failed to run final call summarization: {se}")
            else:
                print(f"Could not find Lead for Call SID: {CallSid} or phone: {To}")

            excel_service.close()
        except Exception as e:
            print(f"Failed to update Call Status in status webhook: {e}")

    return {"success": True}


@router.post("/resume")
async def resume(
    request: Request,
    session_id: str = None,
):
    """
    Called after a 45-second hold pause when Gemini quota was hit.
    Retries the saved pending_transcript and resumes conversation naturally.
    If quota is still exhausted, holds again for another 45 seconds.
    """
    if not session_id:
        session_id = request.query_params.get("session_id")

    response = VoiceResponse()
    session_manager = SessionManager()

    try:
        session = session_manager.get_session(session_id)
    except Exception:
        response.say("Thank you for your patience. Our team will follow up shortly. Goodbye.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    pending_transcript = session.get("pending_transcript") or ""
    gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"

    print(f"[RESUME] Retrying after quota hold. Transcript: '{pending_transcript}'")

    try:
        result = voice_service.process_audio(
            session_id=session_id,
            audio_path=None,
            transcript=pending_transcript,
        )

        # Success — clear hold state
        session["pending_transcript"] = None
        session["on_hold"] = False
        print(f"[RESUME] Gemini responded successfully after hold.")

        # Detect Hindi
        is_hindi = any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in result["reply"])
        session["language"] = "hi" if is_hindi else "en"

        public_base_url = settings.public_base_url
        if not public_base_url:
            public_base_url = str(request.base_url).rstrip("/")

        audio_url = f"{public_base_url}/voice/audio/{result['audio_file']}"

        # Brief resume message then play the AI response
        response.say(
            "Thank you for holding.",
            voice="alice",
            language="en-US",
        )

        if result["end_call"]:
            response.play(audio_url)
            response.hangup()
        else:
            response.play(audio_url)
            gather_lang = "hi-IN" if session.get("language") == "hi" else "en-IN"
            response.gather(
                input="speech",
                speechTimeout="1",
                language=gather_lang,
                action=f"/twilio/process?session_id={session_id}",
                method="POST",
            )

    except Exception as e:
        error_str = str(e)
        print(f"[RESUME] Still quota hit: {error_str}")

        if "Quota" in error_str or "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            # Still quota exhausted — hold for another 45 seconds
            response.say(
                "We appreciate your patience. Just a moment more.",
                voice="alice",
                language="en-US",
            )
            response.pause(length=45)
            response.redirect(
                f"/twilio/resume?session_id={session_id}",
                method="POST",
            )
        else:
            response.say(
                "Thank you for your time. Our team will follow up with you shortly. Goodbye.",
                voice="alice",
            )
            response.hangup()

    return Response(content=str(response), media_type="application/xml")