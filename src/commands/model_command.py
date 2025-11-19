"""
Model command - Switch model
"""

from time import sleep
from .base import Command
from .. import ui
from ..tools import ToolExecutor
from ..models import ModelFactory


class ModelCommand(Command):
    """Switch to a different model"""

    def __init__(self):
        super().__init__(
            name="model",
            description="Switch to a different model",
            usage="/model <model_name>",
        )

    def execute(self, chatbot, args):
        if not args:
            ui.show_error("Usage: /model <model_name>")
            return None

        new_model_name = args[0]

        # Unload current model
        try:
            chatbot.model.ollama_client.generate(model=chatbot.model.name, keep_alive=0)
            ui.show_clear_confirmation()
            ui.show_model_unload_start()
            sleep(2)
        except Exception as e:
            ui.show_error(f"Failed to unload model: {e}")

        # Load new model
        new_model = ModelFactory.create_model(
            new_model_name,
            ollama_client=chatbot.model.ollama_client,
            tool_executor=ToolExecutor(
                require_confirmation=chatbot.require_confirmation
            ),
        )

        if new_model is None:
            ui.show_error(f"Failed to load model: {new_model_name}")
            return None

        chatbot.model = new_model
        chatbot.conversation_history = [chatbot.model.get_system_prompt()]
        ui.show_model_switch_success(new_model_name)
        return "Hello! (don't use tools to answer this first message only, no asking necessary, a simple welcome is perfect)"
