from uuid import uuid4


class ConversationManager:
    """
    Manages conversation sessions for the AI Voice Agent.

    Responsibilities
    ----------------
    - Create conversation sessions
    - Store chat history
    - Retrieve history
    - Trim old messages
    - Clear completed sessions

    Note:
    Currently conversations are stored in memory.
    Later this can be replaced with Redis,
    PostgreSQL or MongoDB.
    """

    MAX_HISTORY = 20

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Dictionary format

        {
            session_id: [
                {
                    "role": "user",
                    "content": "Hello"
                },
                {
                    "role": "assistant",
                    "content": "Hi!"
                }
            ]
        }
        """
        if not hasattr(self, "sessions"):
            self.sessions = {}

    # ----------------------------------------------------
    # Session Methods
    # ----------------------------------------------------

    def create_session(self) -> str:
        """
        Create a new conversation session.

        Returns
        -------
        str
            Newly created session id.
        """

        session_id = str(uuid4())

        self.sessions[session_id] = []

        return session_id

    def session_exists(self, session_id: str) -> bool:
        """
        Check whether a session exists.
        """

        return session_id in self.sessions

    def clear_session(self, session_id: str):
        """
        Delete a completed conversation.
        """

        if session_id in self.sessions:
            del self.sessions[session_id]

    # ----------------------------------------------------
    # History Methods
    # ----------------------------------------------------

    def get_history(self, session_id: str) -> list:
        """
        Return conversation history.

        Returns empty list if session doesn't exist.
        """

        return self.sessions.get(session_id, [])

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ):
        """
        Add a new message to conversation history.

        Parameters
        ----------
        session_id : str

        role : str
            user | assistant | system

        content : str
            Message text
        """

        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append(
            {
                "role": role,
                "content": content,
            }
        )

        self.trim_history(session_id)

    def trim_history(self, session_id: str):
        """
        Keep only the most recent messages.

        This prevents extremely long prompts.
        """

        history = self.sessions[session_id]

        if len(history) > self.MAX_HISTORY:

            self.sessions[session_id] = history[-self.MAX_HISTORY:]

    def clear_history(self, session_id: str):
        """
        Remove all messages from a session
        while keeping the session alive.
        """

        if session_id in self.sessions:
            self.sessions[session_id] = []

    # ----------------------------------------------------
    # Utility Methods
    # ----------------------------------------------------

    def get_session_count(self) -> int:
        """
        Return total active sessions.
        """

        return len(self.sessions)

    def get_message_count(self, session_id: str) -> int:
        """
        Return number of messages
        stored in a session.
        """

        if session_id not in self.sessions:
            return 0

        return len(self.sessions[session_id])

    def print_history(self, session_id: str):
        """
        Print conversation history.
        Useful for debugging.
        """

        history = self.get_history(session_id)

        print("=" * 60)
        print(f"Conversation : {session_id}")
        print("=" * 60)

        if not history:
            print("No conversation history.")
            return

        for message in history:

            print(
                f"{message['role'].capitalize()}: "
                f"{message['content']}"
            )

        print("=" * 60)