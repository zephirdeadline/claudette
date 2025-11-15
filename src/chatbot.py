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


    def manage_user_input(self, user_input: str) -> str:
        if not user_input:
            return "continue"

        if user_input.lower() in ["quit", "exit"]:
            ui.show_goodbye()
            return "break"

        if user_input.lower() == "clear":
            self.conversation_history = [self.model.get_system_prompt()]
            ui.show_clear_confirmation()
            return "continue"

        if user_input.lower() == "history":
            ui.show_history(self.conversation_history)
            return "continue"

        return user_input


    def discuss(self):
        session = PromptSession(history=FileHistory("claudette_history.txt"))
        self.conversation_history.append(self.model.get_system_prompt())
        console = Console()
        while True:
            try:
                # Modern styled prompt
                user_input = session.prompt(
                    HTML("<ansicyan><b>👤 You</b></ansicyan><ansiwhite> ► </ansiwhite>")
                ).strip()
                user_input = self.manage_user_input(user_input)
                if user_input.lower() == "continue":
                    continue
                elif user_input.lower() == "break":
                    sys.exit(0)
                # Get response from the chatbot
                with Live(console=console, refresh_per_second=10, transient=True) as live:
                    response, elapsed = self.chat(live, user_input)
                    ui.show_response(console, elapsed, response)

            except KeyboardInterrupt:
                ui.show_goodbye()
                break
            # except Exception as e:
            #     ui.show_error(str(e))




