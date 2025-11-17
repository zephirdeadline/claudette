"""
Command Manager - Manages all commands and their execution
"""

from typing import Dict, List, TYPE_CHECKING
from .base import Command

# Import all command classes
from .clear_command import ClearCommand
from .conversations_command import ConversationsCommand
from .exit_command import ExitCommand, QuitCommand
from .history_command import HistoryCommand
from .info_command import InfoCommand
from .init_command import InitCommand
from .load_command import LoadCommand
from .model_command import ModelCommand
from .models_command import ModelsCommand, ListCommand
from .prompt_command import PromptCommand
from .pull_command import PullCommand
from .reprompting_command import RepromptingCommand
from .save_command import SaveCommand
from .stats_command import StatsCommand
from .temperature_command import TemperatureCommand
from .thinking_command import ThinkingCommand
from .unload_command import UnloadCommand
from .validate_command import ValidateCommand

if TYPE_CHECKING:
    from ..chatbot import ChatBot


class CommandManager:
    """Manages all available commands"""

    def __init__(self):
        """Initialize the command manager and register all commands"""
        self.commands: Dict[str, Command] = {}
        self._register_commands()

    def _register_commands(self):
        """Register all available commands"""
        commands = [
            ClearCommand(),
            ConversationsCommand(),
            ExitCommand(),
            QuitCommand(),
            HistoryCommand(),
            InfoCommand(),
            InitCommand(),
            ListCommand(),
            LoadCommand(),
            ModelCommand(),
            ModelsCommand(),
            PromptCommand(),
            PullCommand(),
            RepromptingCommand(),
            SaveCommand(),
            StatsCommand(),
            TemperatureCommand(),
            ThinkingCommand(),
            UnloadCommand(),
            ValidateCommand(),
        ]

        for command in commands:
            self.commands[command.name] = command

    def get_command_names(self) -> List[str]:
        """Get a sorted list of all command names with / prefix"""
        return sorted([f"/{name}" for name in self.commands.keys()])

    def execute_command(self, command_input: str, chatbot: "ChatBot") -> str | None:
        """
        Execute a command

        Args:
            command_input: The full command input (e.g., "/model qwen2.5-coder:32b")
            chatbot: The ChatBot instance

        Returns:
            - None: Continue the conversation loop
            - "exit": Exit the application
            - str: The command input if not a command
        """
        if not command_input.startswith("/"):
            return command_input

        # Parse command and arguments
        parts = command_input[1:].split(maxsplit=1)
        command_name = parts[0]
        args = parts[1].split() if len(parts) > 1 else []

        # Check if command exists
        if command_name not in self.commands:
            return command_input

        # Execute command
        command = self.commands[command_name]
        return command.execute(chatbot, args)

    def get_command(self, name: str) -> Command | None:
        """Get a command by name (without /)"""
        return self.commands.get(name)
