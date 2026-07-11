"""
Calls and Automation Router

Contains API endpoints for trigger automation workflows, status tracking,
analytics compilations, and manual meeting bookings.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.crm_service import CRMService
from app.services.session_manager import SessionManager
from app.services.twilio_service import TwilioService

calls_router = APIRouter(
    prefix="/calls",
    tags=["Calls"],
)


class StartCallRequest(BaseModel):
    lead_id: int


@calls_router.post("/start")
def start_call(request: StartCallRequest):
    """
    Triggers an outbound Twilio call for a specific Lead ID.
    Looks up lead info, initializes a customer session, and triggers Twilio.
    """
    crm = CRMService()
    lead = crm.get_lead(request.lead_id)
    if not lead:
        raise HTTPException(
            status_code=404,
            detail=f"Lead with ID {request.lead_id} not found.",
        )

    phone = lead.get("Phone")
    if not phone or str(phone).lower() == "nan":
        raise HTTPException(
            status_code=400,
            detail="Lead does not contain a valid phone number.",
        )

    current_call_status = str(lead.get("Call Status")).strip().lower() if lead.get("Call Status") else ""
    retry_count = lead.get("Retry Count")
    try:
        retry_count = int(retry_count) if retry_count is not None else 0
    except (ValueError, TypeError):
        retry_count = 0

    # Prevent calling if maximum retries reached for automated triggers
    if current_call_status != "pending" and retry_count >= 3:
        raise HTTPException(
            status_code=400,
            detail=f"Lead with ID {request.lead_id} has reached the maximum retry limit of 3.",
        )

    # Clean phone number
    phone_str = str(phone).strip()
    if phone_str.endswith(".0"):
        phone_str = phone_str[:-2]
    phone_str = "".join(c for c in phone_str if c.isdigit() or c == "+")
    
    if len(phone_str) == 10 and not phone_str.startswith("+"):
        phone_str = "+91" + phone_str
    elif not phone_str.startswith("+"):
        phone_str = "+" + phone_str

    # 1. Initialize user session
    session_manager = SessionManager()
    session_id = session_manager.create_session(
        phone=phone_str, lead_id=str(request.lead_id)
    )

    # 2. Trigger Outbound Twilio Call
    try:
        twilio = TwilioService()
        call_sid = twilio.make_call(phone_number=phone_str)

        # Check if this is the first call or a manually scheduled pending call
        last_sid = lead.get("Last Call SID")
        is_first_call = (
            last_sid is None
            or str(last_sid).lower() == "nan"
            or str(last_sid).strip() == ""
        )
        is_manual_pending = current_call_status == "pending"

        updates = {
            "last_call_sid": call_sid,
            "call_status": "Queued"
        }
        if is_first_call or is_manual_pending:
            updates["retry_count"] = 0

        # Update last call SID, status and optionally retry count in Excel CRM
        crm.update_lead(request.lead_id, updates)

        return {
            "success": True,
            "lead_id": request.lead_id,
            "session_id": session_id,
            "call_sid": call_sid,
            "status": "Queued"
        }
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ [CALL TRIGGER FAILED] Lead ID {request.lead_id}: {error_msg}")
        
        # Gracefully update the lead status to 'Failed' in Excel CRM
        try:
            crm.update_lead(request.lead_id, {
                "call_status": "Failed"
            })
        except Exception as ue:
            print(f"⚠️ Failed to update CRM status to Failed: {ue}")

        return {
            "success": False,
            "lead_id": request.lead_id,
            "session_id": None,
            "call_sid": None,
            "status": "Failed",
            "error": error_msg
        }


@calls_router.get("/status")
def get_calls_status():
    """
    Returns active call sessions and their execution progress.
    """
    session_manager = SessionManager()
    return session_manager.list_sessions()
