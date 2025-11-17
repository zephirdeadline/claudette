"""
Unload command - Unload model from VRAM
"""

from .base import Command
from .. import ui


class UnloadCommand(Command):
    """Unload the current model from VRAM"""

    def __init__(self):
        super().__init__(
            name="unload",
            description="Unload the current model from VRAM",
            usage="/unload"
        )

    def execute(self, chatbot, args):
        try:
            # Properly unload the model from VRAM by calling generate with keep_alive=0
            chatbot.model.ollama_client.generate(model=chatbot.model.name, keep_alive=0)
            ui.show_model_unload_success()
            chatbot.model.name = "Unloaded"
        except Exception as e:
            ui.show_error(f"Failed to unload model: {e}")
        return None
