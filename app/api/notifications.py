"""
Notifications Router

Stub endpoints for email and WhatsApp notifications triggered by n8n workflows.
These log notifications locally and are ready to integrate with a real
email/messaging provider (SendGrid, Twilio, etc.) later.
"""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# --------------------------------------------------
# Request Models
# --------------------------------------------------

class EmailRequest(BaseModel):
    email: str
    subject: str
    message: str


class WhatsAppRequest(BaseModel):
    phone: str | int | float
    message: str


# --------------------------------------------------
# In-memory log (for demo — replace with real service)
# --------------------------------------------------

notification_log: list = []


# --------------------------------------------------
# Endpoints
# --------------------------------------------------

@router.post("/email")
def send_email(request: EmailRequest):
    """
    Send an email notification.

    Currently logs locally. Integrate with SendGrid / SES / SMTP to send real emails.
    """
    entry = {
        "type": "email",
        "to": request.email,
        "subject": request.subject,
        "message": request.message,
        "timestamp": datetime.now().isoformat(),
        "status": "logged",
    }
    notification_log.append(entry)

    print(f"\n[EMAIL NOTIFICATION]")
    print(f"  To      : {request.email}")
    print(f"  Subject : {request.subject}")
    print(f"  Message : {request.message[:120]}...")

    return {"success": True, "type": "email", "to": request.email, "status": "logged"}


@router.post("/whatsapp")
def send_whatsapp(request: WhatsAppRequest):
    """
    Send a WhatsApp notification.

    Currently logs locally. Integrate with Twilio WhatsApp API to send real messages.
    """
    # Clean phone string (remove float decimal suffix if any)
    phone_str = str(request.phone).strip()
    if phone_str.endswith(".0"):
        phone_str = phone_str[:-2]

    entry = {
        "type": "whatsapp",
        "to": phone_str,
        "message": request.message,
        "timestamp": datetime.now().isoformat(),
        "status": "logged",
    }
    notification_log.append(entry)

    print(f"\n[WHATSAPP NOTIFICATION]")
    print(f"  To      : {phone_str}")
    print(f"  Message : {request.message[:120]}...")

    return {"success": True, "type": "whatsapp", "to": phone_str, "status": "logged"}


@router.get("/log")
def get_notification_log():
    """Return all logged notifications (useful for debugging)."""
    return {"total": len(notification_log), "notifications": notification_log}
