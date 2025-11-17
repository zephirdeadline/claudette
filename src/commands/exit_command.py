"""
Exit/Quit command
"""

from .base import Command


class ExitCommand(Command):
    """Exit the application"""

    def __init__(self):
        super().__init__(
            name="exit",
            description="Exit the application",
            usage="/exit or /quit"
        )

    def execute(self, chatbot, args):
        return "exit"


class QuitCommand(Command):
    """Quit the application (alias for exit)"""

    def __init__(self):
        super().__init__(
            name="quit",
            description="Quit the application",
            usage="/quit or /exit"
        )

    def execute(self, chatbot, args):
        return "exit"
