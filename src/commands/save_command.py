"""
Save command - Save conversation to file
"""

from .base import Command
from ..utils import save_conversation


class SaveCommand(Command):
    """Save the conversation to a file"""

    def __init__(self):
        super().__init__(
            name="save",
            description="Save the conversation to a file",
            usage="/save [filename]",
        )

    def execute(self, chatbot, args):
        filename = args[0] if args else None
        save_conversation(chatbot.conversation_history, filename)
        return None
