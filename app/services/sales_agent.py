"""
AI Sales Agent

Responsible for:
- Driving the sales conversation
- Qualifying the customer
- Detecting customer intent
- Preparing CRM updates
- Managing conversation state

This service sits between VoiceService and ConversationService.
"""

import re

from app.services.conversation_service import ConversationService
from app.services.session_manager import SessionManager


class SalesAgent:
    """
    Production AI Sales Agent.
    """

    def __init__(self):

        self.conversation = ConversationService()

        self.sessions = SessionManager()

    # -----------------------------------------------------

    def process(
        self,
        session_id: str,
        customer_message: str,
    ):

        self.sessions.add_message(

            session_id,

            "customer",

            customer_message,

        )

        result = self.conversation.chat(

            session_id=session_id,

            customer_message=customer_message,

        )

        self.sessions.add_message(

            session_id,

            "assistant",

            result["response"],

        )

        self.sessions.update_intent(

            session_id,

            result["intent"],

        )

        self.sessions.update_qualification(

            session_id,

            result["qualification"],

        )

        self.sessions.update_summary(

            session_id,

            result["crm_update"]["summary"],

        )

        return {

            "reply": result["response"],

            "intent": result["intent"],

            "qualification": result["qualification"],

            "crm_update": result["crm_update"],

            "end_call": result["end_call"],

        }

    # -----------------------------------------------------

    def extract_email(
        self,
        text: str,
    ):

        pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

        result = re.findall(pattern, text)

        if result:

            return result[0]

        return None

    # -----------------------------------------------------

    def extract_phone(
        self,
        text: str,
    ):

        pattern = r"\+?\d[\d -]{8,15}"

        result = re.findall(pattern, text)

        if result:

            return result[0]

        return None