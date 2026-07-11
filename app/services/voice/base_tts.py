"""
Base Text-to-Speech Interface

Every TTS provider must implement this interface.

Examples
--------
- ElevenLabs
- OpenAI
- Cartesia
"""

from abc import ABC, abstractmethod


class BaseTTS(ABC):
    """
    Abstract base class for every TTS provider.
    """

    @abstractmethod
    def synthesize(
        self,
        text: str,
    ) -> bytes:
        """
        Convert text into speech.

        Parameters
        ----------
        text : str

        Returns
        -------
        bytes
            Audio bytes.
        """
        raise NotImplementedError