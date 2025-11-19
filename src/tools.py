"""
Tools implementation for LLM function calling
"""

from typing import Any, Dict, List
from rich.console import Console
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from .tools_impl import ToolRegistry


class ToolExecutor:
    """Execute tools requested by the LLM"""

    def __init__(self, require_confirmation: bool = True):
        """
        Initialize the tool executor

        Args:
            require_confirmation: Whether to require user confirmation for dangerous operations
        """
        self.require_confirmation = require_confirmation
        self.tool_registry = ToolRegistry(
            require_confirmation=require_confirmation,
            get_confirmation_callback=self._get_confirmation,
        )
        self.tools_definition = self.tool_registry.get_tools_definition()

    def _get_confirmation(self, emoji: str, action: str, details: List[tuple]) -> bool:
        """
        Show a confirmation prompt and get user response.

        Args:
            emoji: Emoji to display (e.g., "⚠", "📝", "✏️")
            action: Action description (e.g., "Command execution", "Create file")
            details: List of (label, value, style) tuples to display

        Returns:
            True if user confirms, False otherwise
        """
        console = Console()
        console.print()

        # Show action header
        warning_text = Text()
        warning_text.append(f"  {emoji} ", style="bold #F59E0B")
        warning_text.append(f"{action}", style="bold #E5E7EB")
        console.print(warning_text)

        # Show details
        for label, value, style in details:
            detail_text = Text()
            detail_text.append(f"    {label}: ", style=style)
            detail_text.append(value, style="#9CA3AF")
            console.print(detail_text)

        session = PromptSession()
        confirmation = (
            session.prompt(HTML('<ansi color="#9CA3AF">    Allow? (Y/n): </ansi>'))
            .strip()
            .lower()
        )
        # Default to 'yes' if user just presses Enter
        return confirmation in ["", "y", "yes"]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            String result of the tool execution
        """
        return self.tool_registry.execute_tool(tool_name, arguments)
