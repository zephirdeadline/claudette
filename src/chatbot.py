"""
ChatBot class - Main chatbot implementation with Ollama integration
"""

import sys
import ollama
from rich.console import Console
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML

from . import ui
from .models import Model

class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, model: Model, ollama_client = ollama.Client):
        """
        Initialize the chatbot

        Args:
            host: Ollama host URL
            model: Model name to use
            image_mode: Enable image processing
            require_confirmation: Require user confirmation for commands
            tool_executor: ToolExecutor instance for handling tool calls
        """
        self.model = model
        self.conversation_history = []
        self.ollama_client = ollama_client

        # Check if Ollama is available


    def chat(self, live: Live, user_message: str) -> (str, float):
        """
        Send a message and get response with tool support

        Args:
            user_message: The user's message

        Returns:
            The assistant's response
        """
        # Prepare user message
        struct_message: dict = self.model.get_user_message(user_message)

        self.conversation_history.append(struct_message)
        #self.display.reset_timer()

        return self.model.process_message(self.conversation_history, live)


    def manage_user_input(self, user_input: str) -> str | None:
        """
        Process user input and handle commands.
        Returns:
            - None: if should continue the loop (skip processing)
            - "exit": if should exit
            - str: the user input to process
        """
        if not user_input:
            return None

        if user_input in ["/quit", "/exit"]:
            return "exit"

        if user_input == "/clear":
            self.conversation_history = [self.model.get_system_prompt()]
            ui.show_clear_confirmation()
            return None

        if user_input == "/history":
            ui.show_history(self.conversation_history)
            return None

        if user_input.startswith("/save"):
            parts = user_input.split(maxsplit=1)
            filename = parts[1] if len(parts) > 1 else None
            self.save_conversation(filename)
            return None

        if user_input.startswith("/load"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                self.load_conversation(parts[1])
            else:
                ui.show_error("Usage: /load <filename>")
            return None

        return user_input

    def _serialize_history(self, history: list) -> list:
        """Convert conversation history to JSON-serializable format"""
        serialized = []
        for msg in history:
            serialized_msg = {}
            for key, value in msg.items():
                if key == "tool_calls":
                    # Convert tool_calls objects to dictionaries
                    serialized_msg[key] = [
                        {
                            "function": {
                                "name": tc.function.name if hasattr(tc.function, 'name') else tc["function"]["name"],
                                "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc["function"]["arguments"]
                            }
                        } if hasattr(tc, 'function') else tc
                        for tc in value
                    ]
                elif key == "images":
                    # Images are already serializable (list of paths)
                    serialized_msg[key] = value
                else:
                    # Copy other fields as-is
                    serialized_msg[key] = value
            serialized.append(serialized_msg)
        return serialized

    def save_conversation(self, filename: str = None):
        """Save conversation history to a file"""
        import json
        import os
        from datetime import datetime

        # Create directory if it doesn't exist
        conversations_dir = ".claudette/conversations"
        os.makedirs(conversations_dir, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        elif not filename.endswith('.json'):
            filename = f"{filename}.json"

        # Full path
        filepath = os.path.join(conversations_dir, filename)

        try:
            # Serialize history to JSON-compatible format
            serialized_history = self._serialize_history(self.conversation_history)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serialized_history, f, indent=2, ensure_ascii=False)
            ui.show_save_confirmation(filepath)
        except Exception as e:
            ui.show_error(f"Failed to save conversation: {str(e)}")

    def load_conversation(self, filename: str):
        """Load conversation history from a file"""
        import json
        import os

        conversations_dir = ".claudette/conversations"

        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        # Full path
        filepath = os.path.join(conversations_dir, filename)

        try:
            if not os.path.exists(filepath):
                ui.show_error(f"File not found: {filepath}")
                return

            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_history = json.load(f)

            self.conversation_history = loaded_history
            ui.show_load_confirmation(filepath, len(loaded_history))
        except json.JSONDecodeError:
            ui.show_error(f"Invalid JSON file: {filepath}")
        except Exception as e:
            ui.show_error(f"Failed to load conversation: {str(e)}")

    def discuss(self):
        session = PromptSession(history=FileHistory("claudette_history.txt"))
        self.conversation_history.append(self.model.get_system_prompt())
        console = Console()

        # Create bottom toolbar function
        def get_bottom_toolbar():
            token_count = ui.get_conversation_token_count(self.conversation_history)
            return HTML(f'<ansi color="#9CA3AF"> Context: {token_count} tokens</ansi>')

        while True:
            try:
                # Minimal modern prompt with bottom toolbar
                user_input = session.prompt(
                    HTML('<ansi color="#9CA3AF">  → </ansi>'),
                    bottom_toolbar=get_bottom_toolbar
                ).strip()

                user_input = self.manage_user_input(user_input)

                if user_input is None:
                    continue
                elif user_input == "exit":
                    break

                # Get response from the chatbot
                with Live(console=console, refresh_per_second=10, transient=True) as live:
                    response, elapsed = self.chat(live, user_input)
                    ui.show_response(console, elapsed, response)

            except KeyboardInterrupt:
                ui.show_goodbye()
                break
        ui.show_goodbye()

            # except Exception as e:
            #     ui.show_error(str(e))




