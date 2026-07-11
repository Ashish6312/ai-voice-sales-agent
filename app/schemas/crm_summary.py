"""
CRM Summary Schema

This schema defines the structured information extracted
from a completed customer conversation.

The AI (Gemini) returns JSON that is validated against
this schema before updating the CRM.
"""

from typing import List

from pydantic import BaseModel, Field


class CRMSummary(BaseModel):
    """
    Structured CRM information extracted by the AI.
    """

    # ----------------------------
    # Customer Information
    # ----------------------------

    customer_name: str = Field(
        default="",
        description="Customer's full name"
    )

    company_name: str = Field(
        default="",
        description="Company name"
    )

    business_type: str = Field(
        default="",
        description="Industry or business type"
    )

    # ----------------------------
    # Qualification
    # ----------------------------

    qualification: str = Field(
        default="Need More Information",
        description="Qualified | Not Qualified | Need More Information"
    )

    interest_level: str = Field(
        default="",
        description="Low | Medium | High"
    )

    decision_maker: str = Field(
        default="",
        description="Whether the customer is the decision maker"
    )

    # ----------------------------
    # Business Requirements
    # ----------------------------

    requirements: List[str] = Field(
        default_factory=list
    )

    pain_points: List[str] = Field(
        default_factory=list
    )

    objections: List[str] = Field(
        default_factory=list
    )

    budget: str = Field(
        default=""
    )

    timeline: str = Field(
        default=""
    )

    # ----------------------------
    # Meeting
    # ----------------------------

    meeting_required: bool = False

    meeting_date: str = ""

    meeting_time: str = ""

    # ----------------------------
    # Follow-up
    # ----------------------------

    follow_up_required: bool = False

    follow_up_date: str = ""

    next_action: str = ""

    # ----------------------------
    # CRM Summary
    # ----------------------------

    summary: str = ""

    # ----------------------------
    # Helper Methods
    # ----------------------------

    def is_qualified(self) -> bool:
        """
        Returns True if the lead is qualified.
        """

        return self.qualification == "Qualified"

    def needs_meeting(self) -> bool:
        """
        Returns True if a meeting is required.
        """

        return self.meeting_required

    def needs_follow_up(self) -> bool:
        """
        Returns True if a follow-up is required.
        """

        return self.follow_up_required