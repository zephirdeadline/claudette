"""
Load command - Load conversation from file
"""

from .base import Command
from .. import ui
from ..utils import load_conversation


class LoadCommand(Command):
    """Load a conversation from a file"""

    def __init__(self):
        super().__init__(
            name="load",
            description="Load a conversation from a file",
            usage="/load <filename>",
        )

    def execute(self, chatbot, args):
        if not args:
            ui.show_error("Usage: /load <filename>")
            return None

        loaded_history = load_conversation(args[0])
        if loaded_history is not None:
            chatbot.conversation_history = loaded_history
        return None
