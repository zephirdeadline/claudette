"""
Base tool class for all LLM tools
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Base class for all tools"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        Initialize a tool

        Args:
            name: Tool name
            description: Description of what the tool does
            parameters: JSON schema for the tool's parameters
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with given arguments

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            String result of the tool execution
        """
        pass

    def get_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for LLM function calling

        Returns:
            Tool definition in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
