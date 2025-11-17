"""
Thinking command - Toggle thinking mode
"""

from .base import Command
from .. import ui


class ThinkingCommand(Command):
    """Toggle thinking mode"""

    def __init__(self):
        super().__init__(
            name="thinking",
            description="Toggle thinking mode",
            usage="/thinking"
        )

    def execute(self, chatbot, args):
        # Toggle thinking mode
        chatbot.enable_thinking = not chatbot.enable_thinking
        ui.show_thinking_change(chatbot.enable_thinking)
        return None
