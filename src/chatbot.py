"""
ChatBot class - Main chatbot implementation with Ollama integration
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ollama import ResponseError
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.live import Live

from . import ui
from .commands import CommandManager
from .completers import CommandAndFileCompleter
from .models import Model
from .utils import get_git_branch


class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, model: Model) -> None:
        """
        Initialize the chatbot

        Args:
            model: Model instance to use for chat interactions
        """
        self.model: Model = model
        self.conversation_history: List[Dict[str, any]] = []
        self.temperature: float = 0.0
        self.require_confirmation: bool = (
            self.model.tool_executor.require_confirmation
            if self.model.tool_executor
            else True
        )
        self.enable_thinking: bool = False
        self.enable_reprompting: bool = False
        self.command_manager: CommandManager = CommandManager()

    def _reprompt_user_message(self, user_message: str) -> str:
        """
        Rewrite user message to be more comprehensible for the LLM

        Args:
            user_message: Original user message

        Returns:
            Rewritten user message
        """
        # Build the reprompting instruction with context from the main LLM's system prompt
        llm_context = f"""
TARGET LLM SYSTEM PROMPT CONTEXT:
The user's message will be processed by an LLM with the following system prompt constraints and capabilities:

{self.model.system_prompt}

---"""

        reprompt_instruction = {
            "role": "system",
            "content": f"""{llm_context}

You are a prompt optimization assistant. Your task is to rewrite the user's input to make it clearer and more comprehensible for the target LLM assistant described above.

CRITICAL INSTRUCTIONS:
- Take into account the TARGET LLM's system prompt, capabilities, and constraints when rewriting
- Align the rewritten message with the LLM's expected behavior and protocols
- If the LLM has specific protocols (e.g., "CRITICAL - Action Explanation", "Type Annotations", "AGENTS.md awareness"), ensure the rewritten prompt respects these
- Keep the same intent and meaning as the original message
- Make it more explicit and detailed
- Add context if needed (project context, technical details, etc.)
- Fix grammar and spelling errors
- Make it more structured if it's vague
- Keep it concise but clear and actionable
- If the message is already clear and aligned with the LLM's protocols, return it unchanged
- ONLY return the rewritten message, nothing else (no explanations, no meta-commentary)

CRITICAL - PERSPECTIVE AND VOICE:
- ALWAYS keep the USER'S perspective in the rewritten message
- NEVER switch to first-person "I" from the assistant's perspective
- The rewritten message should be a USER REQUEST, not an assistant statement
- Use imperative form ("Do this", "Check that") or question form ("Can you...", "Please...")
- NEVER use "I will..." or "I'm going to..." - these are assistant phrases, not user requests

EXAMPLES:
Original: "fix the bug"
Rewritten: "Identify and fix the bug in the current codebase. Please explain what you're going to do before making changes, verify the fix works, and ensure all imports are at the top of the file."

Original: "add email validation"
Rewritten: "Add email validation functionality. First check if AGENTS.md exists to see if there's already a validation utility we can extend. Use proper Python type hints for all functions."

Original: "cherche sur le web les dernières news"
Rewritten: "Recherche sur le web les dernières actualités. Utilise l'outil web_search pour trouver les informations les plus récentes et présente-les de manière structurée."
WRONG: "Je vais rechercher sur le web les dernières actualités..." (NEVER use "Je vais")

Original: "Hello, how are you?"
Rewritten: "Hello, how are you?" (unchanged - already clear)
""",
        }

        temp_history = [
            reprompt_instruction,
            {
                "role": "user",
                "content": f"Reprompt, transform, keep the meaning of the user question and return only the result, nothing more {reprompt_instruction}: <UserMessage>{user_message}</UserMessage>",
            },
        ]

        # Use streaming call for reprompting with live animation
        from time import time
        from rich.live import Live
        from rich.console import Console

        start_time = time()
        reprompted_message = ""

        console = Console()

        # Start streaming with live animation
        with Live(console=console, refresh_per_second=10, transient=True) as live:
            for chunk in self.model.ollama_client.chat(
                model=self.model.name,
                messages=temp_history,
                options={"temperature": 0.3},
                stream=True,
            ):
                # Get content from chunk
                message = chunk.get("message", {})
                if content := message.get("content"):
                    reprompted_message += content

                # Update live display with animation and token count
                ui.show_reprompting_animation(reprompted_message, live, start_time)

        elapsed_time = time() - start_time

        # Calculate total tokens using the tokenizer
        total_tokens = ui.get_token_count(reprompted_message)

        # Log reprompting statistics
        self.model.stats_manager.update_stats(
            model_name=self.model.name,
            thinking_tokens=0,  # No thinking in reprompting
            response_tokens=total_tokens,
            time_seconds=elapsed_time,
            is_reprompting=True,
        )

        # Show the reprompted version to the user with token info
        if reprompted_message != user_message:
            ui.show_reprompted_message(
                user_message, reprompted_message, total_tokens, elapsed_time
            )

        return reprompted_message

    def chat(self, live: Live, user_message: str) -> Tuple[str, float, str]:
        """
        Send a message and get response with tool support

        Args:
            live: Rich Live display instance
            user_message: The user's message

        Returns:
            Tuple of (response, elapsed_time, thinking_content)
        """
        # Apply reprompting if enabled
        if self.enable_reprompting:
            user_message = self._reprompt_user_message(user_message)

        # Prepare user message
        struct_message: Dict[str, any] = self.model.get_user_message(user_message)

        self.conversation_history.append(struct_message)

        return self.model.process_message(
            self.conversation_history, live, self.temperature, self.enable_thinking
        )

    def manage_user_input(self, user_input: str) -> Optional[str]:
        """
        Process user input and handle commands

        Args:
            user_input: User's input string

        Returns:
            - None: if should continue the loop (skip processing)
            - "exit": if should exit
            - str: the user input to process
        """
        if not user_input:
            return None

        # Use CommandManager to handle all commands
        return self.command_manager.execute_command(user_input, self)

    def discuss(self) -> None:
        """
        Main discussion loop for interactive chat

        Handles user input, command execution, and displays responses
        """
        # Create combined completer for commands (/) and files (@)
        combined_completer: CommandAndFileCompleter = CommandAndFileCompleter(
            self.command_manager.get_command_names()
        )

        # Setup history file in user's home .claudette directory
        history_dir: Path = Path.home() / ".claudette"
        history_dir.mkdir(exist_ok=True)
        history_file: Path = history_dir / "claudette_history.txt"

        # Create key bindings for Enter=submit, Alt+Enter=newline
        kb: KeyBindings = KeyBindings()

        @kb.add("enter")
        def _(event):
            event.current_buffer.validate_and_handle()

        @kb.add("escape", "enter")  # Alt+Enter (more reliable than Shift+Enter)
        def _(event):
            event.current_buffer.insert_text("\n")

        session: PromptSession = PromptSession(
            history=FileHistory(str(history_file)),
            completer=combined_completer,
            complete_while_typing=True,
            key_bindings=kb,
        )
        self.conversation_history.append(self.model.get_system_prompt())
        console: Console = Console()

        # Create bottom toolbar function
        def get_bottom_toolbar():
            token_count = ui.get_conversation_token_count(self.conversation_history)

            # Build toolbar components
            toolbar_parts = []

            # Add current directory with folder emoji (full path)
            cwd = os.getcwd()
            toolbar_parts.append(f"📁 {cwd}")

            # Add git branch if available with branch emoji
            branch = get_git_branch()
            if branch:
                toolbar_parts.append(f"🌿 {branch}")

            # Add model name with robot emoji
            toolbar_parts.append(f"🤖 {self.model.name}")

            # Add vision support indicator with camera emoji
            if self.model.image_mode:
                toolbar_parts.append('<ansi color="#10B981">📷 ON</ansi>')
            else:
                toolbar_parts.append('<ansi color="#6B7280">📷 OFF</ansi>')

            # Add tools support indicator with wrench emoji
            if self.model.tool_executor and self.model.tool_executor.tools_definition:
                toolbar_parts.append(f'<ansi color="#10B981">🔧 ON</ansi>')
            else:
                toolbar_parts.append('<ansi color="#6B7280">🔧 OFF</ansi>')

            # Add temperature with thermometer emoji
            toolbar_parts.append(f"🌡️ {self.temperature}")

            # Add validation status with shield emoji
            if self.require_confirmation:
                toolbar_parts.append('<ansi color="#10B981">🛡️ ON </ansi>')
            else:
                toolbar_parts.append('<ansi color="#EF4444">🛡️ OFF </ansi>')

            # Add thinking mode status with brain emoji
            if self.enable_thinking:
                toolbar_parts.append('<ansi color="#10B981">🧠 ON </ansi>')
            else:
                toolbar_parts.append('<ansi color="#6B7280">🧠 OFF </ansi>')

            # Add reprompting mode status with sparkles emoji
            if self.enable_reprompting:
                toolbar_parts.append('<ansi color="#F59E0B">✨ ON </ansi>')
            else:
                toolbar_parts.append('<ansi color="#6B7280">✨ OFF </ansi>')

            # Add token count with percentage and status indicator
            max_context = self.model.max_token_context
            percentage = (token_count / max_context * 100) if max_context > 0 else 0

            # Choose status indicator based on percentage
            if percentage < 50:
                status = "<ansi>🟢</ansi>"  # Green - Low usage
            elif percentage < 80:
                status = "<ansi>🟡</ansi>"  # Amber - Medium usage
            else:
                status = "<ansi>🔴</ansi>"  # Red - High usage

            toolbar_parts.append(
                f"{status} {token_count}/{max_context} ({percentage:.1f}%)"
            )

            return HTML(f'<ansi color="#9CA3AF"> {" | ".join(toolbar_parts)}</ansi>')

        while True:
            try:
                # Minimal modern prompt with bottom toolbar and autocompletion
                user_input = session.prompt(
                    HTML('<ansi color="#9CA3AF">  → </ansi>'),
                    bottom_toolbar=get_bottom_toolbar,
                    multiline=True,
                ).strip()

                user_input = self.manage_user_input(user_input)

                if user_input is None:
                    continue
                elif user_input == "exit":
                    break
                try:
                    # Get response from the chatbot
                    with Live(
                        console=console, refresh_per_second=10, transient=True
                    ) as live:
                        response, elapsed, thinking_content = self.chat(
                            live, user_input
                        )
                        ui.show_response(console, elapsed, response, thinking_content)
                except ResponseError as e:
                    ui.show_error(f"Model {self.model.name} not found! {e}")

            except KeyboardInterrupt:
                ui.show_goodbye()
                break
