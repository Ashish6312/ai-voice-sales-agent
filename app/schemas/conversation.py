"""
Conversation Schemas

Schemas used for ending a conversation
and updating the CRM.
"""

from pydantic import BaseModel


class EndConversationRequest(BaseModel):
    """
    Request sent when a conversation finishes.
    """

    session_id: str
    lead_id: int


class EndConversationResponse(BaseModel):
    """
    Response after CRM update.
    """

    success: bool
    message: str