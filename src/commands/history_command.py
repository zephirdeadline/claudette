"""
History command - Show conversation history
"""

from .base import Command
from .. import ui


class HistoryCommand(Command):
    """Show the conversation history"""

    def __init__(self):
        super().__init__(
            name="history",
            description="Show the conversation history",
            usage="/history",
        )

    def execute(self, chatbot, args):
        ui.show_history(chatbot.conversation_history)
        return None
