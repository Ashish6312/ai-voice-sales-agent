from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    Incoming chat request.
    """

    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """
    AI response.
    """

    session_id: str
    response: str