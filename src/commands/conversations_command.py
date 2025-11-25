"""
Conversations command - List saved conversations
"""

import os
from .base import Command
from .. import ui


class ConversationsCommand(Command):
    """List all saved conversations"""

    def __init__(self):
        super().__init__(
            name="conversations",
            description="List all saved conversations",
            usage="/conversations",
        )

    def execute(self, chatbot, args):
        try:
            from ..utils.paths import get_conversations_dir
            conversations_dir = str(get_conversations_dir())

            if not os.path.exists(conversations_dir):
                ui.show_error(f"No conversations directory found: {conversations_dir}")
                return None

            # Get list of conversation files
            conversation_files = []
            for filename in os.listdir(conversations_dir):
                if filename.endswith(".yaml"):
                    filepath = os.path.join(conversations_dir, filename)
                    stat = os.stat(filepath)
                    conversation_files.append(
                        {
                            "name": filename,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        }
                    )

            ui.show_conversations_list(conversation_files)
        except Exception as e:
            ui.show_error(f"Failed to list conversations: {e}")
        return None
