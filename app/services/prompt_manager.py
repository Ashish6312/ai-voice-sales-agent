from pathlib import Path


class PromptManager:
    """
    PromptManager is responsible for loading and managing
    all prompt templates used by the AI Voice Sales Agent.

    Responsibilities:
    - Load prompt files
    - Cache prompts in memory
    - Return prompts on request
    """

    def __init__(self):

        self.prompt_dir = Path("app/prompts")

        self._cache = {}

    def _load_prompt(self, filename: str) -> str:
        """
        Load a prompt file.

        If already loaded,
        return it from cache.
        """

        if filename in self._cache:
            return self._cache[filename]

        prompt_path = self.prompt_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file '{filename}' not found."
            )

        prompt = prompt_path.read_text(
            encoding="utf-8"
        )

        self._cache[filename] = prompt

        return prompt

    def get_system_prompt(self) -> str:
        """
        Load the system prompt.
        """

        return self._load_prompt(
            "system_prompt.txt"
        )

    def get_qualification_prompt(self) -> str:
        """
        Load the qualification prompt.
        """

        return self._load_prompt(
            "qualification_prompt.txt"
        )

    def get_objection_prompt(self) -> str:
        """
        Load the objection handling prompt.
        """

        return self._load_prompt(
            "objection_prompt.txt"
        )

    def get_summary_prompt(self) -> str:
        """
        Load the CRM summary prompt.
        """

        return self._load_prompt(
            "summary_prompt.txt"
        )

    def clear_cache(self):
        """
        Clear cached prompts.

        Useful during development.
        """

        self._cache.clear()