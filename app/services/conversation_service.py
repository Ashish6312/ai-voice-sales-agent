"""
Conversation Service

This service orchestrates the complete customer conversation workflow.

Responsibilities
----------------
1. Retrieve conversation history.
2. Search the knowledge base (RAG).
3. Generate AI response.
4. Save conversation.
5. Generate CRM summary.
6. Update Excel CRM.
"""

from app.services.ai_service import AIService
from app.services.conversation_manager import ConversationManager
from app.services.crm_service import CRMService
from app.services.knowledge_service import KnowledgeService


class ConversationService:
    """
    Main business workflow of the application.

    This class connects all backend services together.
    """

    def __init__(self):

        self.ai_service = AIService()

        self.knowledge_service = KnowledgeService()

        self.knowledge_service.load_index()

        self.conversation_manager = ConversationManager()

        self.crm_service = CRMService()

    # --------------------------------------------------
    # Chat
    # --------------------------------------------------

    def chat(
        self,
        session_id: str,
        customer_message: str,
    ) -> dict:
        """
        Process one customer message.

        Returns
        -------
        dict
        """

        # -----------------------------
        # Conversation History
        # -----------------------------

        history = self.conversation_manager.get_history(
            session_id
        )

        # -----------------------------
        # RAG Search
        # -----------------------------

        context_chunks = self.knowledge_service.search(
            customer_message
        )

        context = "\n\n".join(context_chunks)

        # -----------------------------
        # Gemini
        # -----------------------------

        result = self.ai_service.generate_sales_response(

            history=history,

            customer_message=customer_message,

            context=context,

        )

        # -----------------------------
        # Save Customer Message
        # -----------------------------

        self.conversation_manager.add_message(

            session_id,

            "user",

            customer_message,

        )

        # -----------------------------
        # Save AI Message
        # -----------------------------

        self.conversation_manager.add_message(

            session_id,

            "assistant",

            result["reply"],

        )

        # -----------------------------
        # Return
        # -----------------------------

        return {

            "response": result["reply"],

            "intent": result["intent"],

            "qualification": result["qualification"],

            "crm_update": result["crm_update"],

            "end_call": result["end_call"],

            "context": context,

            "history": self.conversation_manager.get_history(
                session_id
            ),

        }

    # --------------------------------------------------
    # End Conversation
    # --------------------------------------------------

    def end_conversation(
        self,
        session_id: str,
        lead_id: int,
    ):
        """
        Finish a conversation.

        Generates CRM summary
        and updates Excel.
        """

        history = self.conversation_manager.get_history(
            session_id
        )

        conversation = ""

        for chat in history:

            conversation += (
                f"{chat['role'].title()}: "
                f"{chat['content']}\n"
            )

        summary = self.ai_service.generate_summary(
            conversation
        )

        crm_update = {
            "qualification": summary.qualification,
            "summary": summary.summary,
            "objection": ", ".join(summary.objections) if summary.objections else "",
            "requirement": ", ".join(summary.requirements) if summary.requirements else "",
            "meeting": f"{summary.meeting_date} {summary.meeting_time}".strip(),
            "follow_up": summary.follow_up_date,
            "status": "Interested" if (summary.meeting_required or summary.meeting_date) else "Contacted"
        }

        self.crm_service.update_lead(
            lead_id=lead_id,
            crm_update=crm_update,
        )

        return summary