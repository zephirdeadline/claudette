"""
ChatBot class - Main chatbot implementation with Ollama integration
"""

import sys
import subprocess
from time import sleep

import ollama
from rich.console import Console
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter

from . import ui
from .models import Model, ModelFactory


def get_git_branch() -> str | None:
    """
    Get the current git branch name.

    Returns:
        The current branch name or None if not in a git repository
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=1,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None

class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, model: Model):
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
        self.temperature = 0
        self.require_confirmation = self.model.tool_executor.require_confirmation

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

        return self.model.process_message(self.conversation_history, live, self.temperature)


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

        if user_input.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                ui.show_error("Usage: /model <model_name>")
                return None

            new_model_name = parts[1]

            # Unload current model
            try:
                self.model.ollama_client.generate(model=self.model.name, keep_alive=0)
                ui.show_clear_confirmation()
                ui.show_model_unload_start()
                sleep(2)
            except Exception as e:
                ui.show_error(f"Failed to unload model: {e}")

            # Load new model
            from .models import ModelFactory
            new_model = ModelFactory.create_model(
                new_model_name,
                ollama_client=self.model.ollama_client,
                tool_executor=self.model.tool_executor
            )

            if new_model is None:
                ui.show_error(f"Failed to load model: {new_model_name}")
                return None

            self.model = new_model
            self.conversation_history = [self.model.get_system_prompt()]
            ui.show_model_switch_success(new_model_name)


        if user_input.startswith("/unload"):
            try:
                # Properly unload the model from VRAM by calling generate with keep_alive=0
                self.model.ollama_client.generate(model=self.model.name, keep_alive=0)
                ui.show_model_unload_success()
                self.model.name = "Unloaded"
            except Exception as e:
                ui.show_error(f"Failed to unload model: {e}")
            return None

        if user_input.startswith("/pull"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                ui.show_error("Usage: /pull <model_name>")
                return None

            model_name = parts[1]
            ui.show_pull_start(model_name)

            try:
                # Pull model with streaming progress
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
                console = Console()

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Downloading {model_name}", total=None)

                    for chunk in self.model.ollama_client.pull(model_name, stream=True):
                        if 'total' in chunk and 'completed' in chunk:
                            progress.update(task, total=chunk['total'], completed=chunk['completed'])
                        elif 'status' in chunk:
                            progress.update(task, description=f"{chunk['status']}")

                ui.show_pull_success(model_name)

            except Exception as e:
                ui.show_error(f"Failed to pull model: {e}")

            return None

        if user_input.startswith("/info"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                ui.show_error("Usage: /info <model_name>")
                return None

            model_name = parts[1]

            try:
                # Get model info from Ollama
                model_info = self.model.ollama_client.show(model_name)
                ui.show_model_info(model_name, model_info)

            except Exception as e:
                ui.show_error(f"Failed to get model info: {e}")

            return None

        if user_input.startswith("/temperature"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                ui.show_error(f"Current temperature: {self.temperature}\nUsage: /temperature <value> (0.0 to 2.0)")
                return None

            try:
                new_temp = float(parts[1])
                if not 0.0 <= new_temp <= 2.0:
                    ui.show_error("Temperature must be between 0.0 and 2.0")
                    return None

                self.temperature = new_temp
                ui.show_temperature_change(new_temp)
            except ValueError:
                ui.show_error("Temperature must be a number")

            return None

        if user_input == "/validate":
            # Toggle validation status
            current_status = self.model.tool_executor.require_confirmation
            self.model.tool_executor.require_confirmation = not current_status
            self.require_confirmation = self.model.tool_executor.require_confirmation
            ui.show_validation_change(self.require_confirmation)
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
        # Create command completer
        commands = ['/exit', '/quit', '/clear', '/history', '/save', '/load', '/model', '/unload', '/pull', '/info', '/temperature', '/validate']
        command_completer = WordCompleter(
            commands,
            ignore_case=True,
            sentence=True,
            match_middle=False
        )

        session = PromptSession(
            history=FileHistory("claudette_history.txt"),
            completer=command_completer,
            complete_while_typing=True
        )
        self.conversation_history.append(self.model.get_system_prompt())
        console = Console()

        # Create bottom toolbar function
        def get_bottom_toolbar():
            import os
            token_count = ui.get_conversation_token_count(self.conversation_history)

            # Build toolbar components
            toolbar_parts = []

            # Add current directory with folder emoji (full path)
            cwd = os.getcwd()
            toolbar_parts.append(f'📁 {cwd}')

            # Add git branch if available with branch emoji
            branch = get_git_branch()
            if branch:
                toolbar_parts.append(f'🌿 {branch}')

            # Add model name with robot emoji
            toolbar_parts.append(f'🤖 {self.model.name}')

            # Add temperature with thermometer emoji
            toolbar_parts.append(f'🌡️ {self.temperature}')

            # Add validation status with shield emoji
            if self.require_confirmation:
                toolbar_parts.append('<ansi color="#10B981">🛡️ ON </ansi>')
            else:
                toolbar_parts.append('<ansi color="#EF4444">🛡️ OFF </ansi>')

            # Add token count with percentage and status indicator
            max_context = self.model.max_token_context
            percentage = (token_count / max_context * 100) if max_context > 0 else 0

            # Choose status indicator based on percentage
            if percentage < 50:
                status = '<ansi>🟢</ansi>'  # Green - Low usage
            elif percentage < 80:
                status = '<ansi>🟡</ansi>'  # Amber - Medium usage
            else:
                status = '<ansi>🔴</ansi>'  # Red - High usage

            toolbar_parts.append(f'{status} {token_count}/{max_context} ({percentage:.1f}%)')

            return HTML(f'<ansi color="#9CA3AF"> {" | ".join(toolbar_parts)}</ansi>')

        while True:
            try:
                # Minimal modern prompt with bottom toolbar and autocompletion
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




