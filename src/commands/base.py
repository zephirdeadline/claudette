"""
Base command class for all commands
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..chatbot import ChatBot


class Command(ABC):
    """Base class for all commands"""

    def __init__(self, name: str, description: str, usage: str = None):
        """
        Initialize a command

        Args:
            name: Command name (without the /)
            description: Brief description of what the command does
            usage: Optional usage string (e.g., "/command <arg>")
        """
        self.name = name
        self.description = description
        self.usage = usage or f"/{name}"

    @abstractmethod
    def execute(self, chatbot: "ChatBot", args: list[str]) -> str | None:
        """
        Execute the command

        Args:
            chatbot: The ChatBot instance
            args: List of arguments passed to the command

        Returns:
            - None: Continue the conversation loop
            - "exit": Exit the application
            - str: Any other return value for special handling
        """
        pass

    def get_name_with_slash(self) -> str:
        """Get the command name with the / prefix"""
        return f"/{self.name}"
