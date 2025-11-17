"""
Models/List command - List available models
"""

from .base import Command
from .. import ui


class ModelsCommand(Command):
    """List all available models"""

    def __init__(self):
        super().__init__(
            name="models",
            description="List all available models",
            usage="/models or /list"
        )

    def execute(self, chatbot, args):
        try:
            models_response = chatbot.model.ollama_client.list()
            ui.show_models_list(models_response)
        except Exception as e:
            ui.show_error(f"Failed to list models: {e}")
        return None


class ListCommand(Command):
    """List all available models (alias for /models)"""

    def __init__(self):
        super().__init__(
            name="list",
            description="List all available models",
            usage="/list or /models"
        )

    def execute(self, chatbot, args):
        try:
            models_response = chatbot.model.ollama_client.list()
            ui.show_models_list(models_response)
        except Exception as e:
            ui.show_error(f"Failed to list models: {e}")
        return None
