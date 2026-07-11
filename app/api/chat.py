"""
Chat API

Thin Controller

Responsibilities
----------------
1. Receive HTTP request
2. Call ConversationService
3. Return HTTP response

No business logic should exist here.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):
    """
    Process a customer message.
    """

    try:
        from app.services.conversation_service import ConversationService
        conversation_service = ConversationService()

        result = conversation_service.chat(

            session_id=request.session_id,

            customer_message=request.message,
        )

        return ChatResponse(

            session_id=request.session_id,

            response=result["response"],

            qualification="",

            meeting_required=False,

            follow_up_required=False,
        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e),
        )