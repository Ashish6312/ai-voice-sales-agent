"""
Conversation API

Handles conversation completion.

Responsibilities
----------------
1. Generate CRM summary.
2. Update Excel.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.conversation import (
    EndConversationRequest,
    EndConversationResponse,
)

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"],
)


@router.post(
    "/end",
    response_model=EndConversationResponse,
)
def end_conversation(
    request: EndConversationRequest,
):
    """
    End a customer conversation.
    """

    try:
        from app.services.conversation_service import ConversationService
        conversation_service = ConversationService()

        summary = conversation_service.end_conversation(

            session_id=request.session_id,

            lead_id=request.lead_id,
        )

        return EndConversationResponse(

            success=True,

            message=f"Conversation completed. Lead marked as {summary.qualification}.",
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )