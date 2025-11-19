"""
Info command - Show model information
"""

from .base import Command
from .. import ui


class InfoCommand(Command):
    """Show information about a model"""

    def __init__(self):
        super().__init__(
            name="info",
            description="Show information about a model",
            usage="/info <model_name>",
        )

    def execute(self, chatbot, args):
        if not args:
            ui.show_error("Usage: /info <model_name>")
            return None

        model_name = args[0]

        try:
            # Get model info from Ollama
            model_info = chatbot.model.ollama_client.show(model_name)
            ui.show_model_info(model_name, model_info)

        except Exception as e:
            ui.show_error(f"Failed to get model info: {e}")

        return None
