"""
Reprompting command - Toggle reprompting mode
"""

from .base import Command
from .. import ui


class RepromptingCommand(Command):
    """Toggle reprompting mode (rewrites user input for better LLM understanding)"""

    def __init__(self):
        super().__init__(
            name="reprompting",
            description="Toggle reprompting mode to rewrite user input for better LLM comprehension",
            usage="/reprompting"
        )

    def execute(self, chatbot, args):
        # Toggle reprompting mode
        chatbot.enable_reprompting = not chatbot.enable_reprompting
        ui.show_reprompting_change(chatbot.enable_reprompting)
        return None
