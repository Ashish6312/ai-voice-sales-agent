"""
Session Manager

This service manages active customer conversation states in memory.
Every active call corresponds to a unique session which holds the state of the conversation.

Design Pattern:
---------------
- Singleton Pattern: Inherits __new__ to ensure that only a single instance of SessionManager 
  exists across the entire application runtime. All calls and API routers access the exact 
  same self.sessions dictionary in RAM.

Data Stored Per Session:
------------------------
1. Customer Phone (str): Cleaned telephone number.
2. Lead ID (int | None): Key mapping to Leads.xlsx row.
3. Conversation History (list): Appends dictionaries of {"role": "customer"|"assistant", "message": "...", "time": "..."} 
   to pass as context to the Gemini LLM.
4. Lead Qualification (str): Warm / Cold / Hot.
5. Intent (str): User's identified intent.
6. Summary (str): Running call summary.
7. CRM (dict): Fields scheduled for update on the spreadsheet.
"""

from datetime import datetime
from uuid import uuid4


class SessionManager:
    """
    In-memory Singleton Session Manager to maintain call states across concurrent webhooks.
    """

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance.sessions = {}

        return cls._instance

    # -------------------------------------------------

    def create_session(
        self,
        phone: str,
        lead_id: str | None = None,
    ) -> str:
        """
        Create a new customer session.
        """

        session_id = str(uuid4())

        self.sessions[session_id] = {

            "session_id": session_id,

            "lead_id": lead_id,

            "phone": phone,

            "created_at": datetime.now(),

            "last_updated": datetime.now(),

            "history": [],

            "qualification": "Unknown",

            "intent": None,

            "meeting": None,

            "summary": "",

            "ended": False,

            "last_audio": None,

            "crm": {},

            # Hold-and-retry support: stores transcript when quota is hit
            "pending_transcript": None,
            "on_hold": False,

            # Async AI processing support
            "ai_result": None,
            "ai_error": None,
            "ai_processing": False,
            "public_base_url": None,
        }

        return session_id

    # -------------------------------------------------

    def exists(
        self,
        session_id: str,
    ) -> bool:

        return session_id in self.sessions

    # -------------------------------------------------

    def get_session(
        self,
        session_id: str,
    ) -> dict:

        if session_id not in self.sessions:

            raise ValueError(
                f"Session not found: {session_id}"
            )

        return self.sessions[session_id]

    # -------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        message: str,
    ):

        session = self.get_session(session_id)

        session["history"].append({

            "role": role,

            "message": message,

            "time": datetime.now().isoformat(),

        })

        session["last_updated"] = datetime.now()

    # -------------------------------------------------

    def update_intent(
        self,
        session_id: str,
        intent: str,
    ):

        self.sessions[session_id]["intent"] = intent

    # -------------------------------------------------

    def update_qualification(
        self,
        session_id: str,
        qualification: str,
    ):

        self.sessions[session_id][
            "qualification"
        ] = qualification

    # -------------------------------------------------

    def update_summary(
        self,
        session_id: str,
        summary: str,
    ):

        self.sessions[session_id][
            "summary"
        ] = summary

    # -------------------------------------------------

    def schedule_meeting(
        self,
        session_id: str,
        meeting: str,
    ):

        self.sessions[session_id][
            "meeting"
        ] = meeting

    # -------------------------------------------------

    def end_session(
        self,
        session_id: str,
    ):

        self.sessions[session_id]["ended"] = True

        self.sessions[session_id][
            "last_updated"
        ] = datetime.now()

    # -------------------------------------------------

    def delete_session(
        self,
        session_id: str,
    ):

        if session_id in self.sessions:

            del self.sessions[session_id]

    # -------------------------------------------------

    def list_sessions(self):

        return list(
            self.sessions.values()
        )