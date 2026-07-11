from typing import Optional

from pydantic import BaseModel


class Lead(BaseModel):
    """
    Represents one lead in our CRM.
    """

    lead_id: int

    name: str

    phone: str

    status: str

    call_status: Optional[str] = None

    qualification: Optional[str] = None

    summary: Optional[str] = None

    requirements: Optional[str] = None

    objections: Optional[str] = None

    follow_up_date: Optional[str] = None

    meeting_date: Optional[str] = None

    last_contacted: Optional[str] = None