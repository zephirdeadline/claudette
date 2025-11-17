"""
Validate command - Toggle validation/confirmation mode
"""

from .base import Command
from .. import ui


class ValidateCommand(Command):
    """Toggle validation/confirmation mode for tools"""

    def __init__(self):
        super().__init__(
            name="validate",
            description="Toggle validation/confirmation mode for tools",
            usage="/validate"
        )

    def execute(self, chatbot, args):
        # Toggle validation status
        current_status = chatbot.model.tool_executor.require_confirmation
        chatbot.model.tool_executor.require_confirmation = not current_status
        chatbot.require_confirmation = chatbot.model.tool_executor.require_confirmation
        ui.show_validation_change(chatbot.require_confirmation)
        return None
