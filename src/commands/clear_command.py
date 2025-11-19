"""
Clear command - Clear conversation history
"""

from .base import Command
from .. import ui


class ClearCommand(Command):
    """Clear the conversation history"""

    def __init__(self):
        super().__init__(
            name="clear", description="Clear the conversation history", usage="/clear"
        )

    def execute(self, chatbot, args):
        chatbot.conversation_history = [chatbot.model.get_system_prompt()]
        ui.show_clear_confirmation()
        return None
