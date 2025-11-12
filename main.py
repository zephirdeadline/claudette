#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
"""

import json
import re
import base64
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Any
import ollama
from colorama import Fore, Style, init
from tools import ToolExecutor
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML 
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text

# Initialize colorama for colored output
init(autoreset=True)


class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, host: str,  model: str, image_mode: bool, require_confirmation: bool = True):
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = [
                {
                    'role': 'system',
                    'content': '''You are an expert coding assistant with access to the user's local development environment.

  Core Capabilities:
  - Read, write, and edit files in the project directory
  - Execute system commands and tools available on the user's computer
  - Provide well-researched, accurate technical responses

  Behavior Guidelines:
  - When users reference files, proactively read/write/edit them
  - Auto-correct minor typos in file paths without mentioning them
  - Treat short responses ("ok", "yes", "do it") as confirmation to proceed with your last proposal
  - Use available system commands freely as needed for the task
  - Verify technical accuracy before responding

  Project Work Best Practices:
  - ALWAYS explore the codebase first before making changes (check existing patterns, conventions, dependencies)
  - Read relevant files to understand context before modifying code
  - Maintain consistency with existing code style, architecture, and naming conventions
  - Check for related files (tests, configs, docs) that may need updates
  - Verify changes don't break existing functionality
  - Provide clear explanations of what you're doing and why
  - When unsure, ask clarifying questions before proceeding
  - After changes, suggest testing steps or commands to verify the work

  Error Handling:
  - If a command fails, analyze the error and attempt to fix it
  - Don't repeat the same failing command without modifications
  - Look for logs, error messages, or stack traces to diagnose issues

  You have full access to the local environment - use whatever tools and commands are necessary to help the user effectively.'''
  }
                ]
        self.tool_executor = ToolExecutor(require_confirmation=require_confirmation)
        self.host = host
        self.ollama_client = ollama.Client(host=host)
        self.start_time = time.time()
        self.image_mode = image_mode
        self.elapsed = 0
        # Check if Ollama is available
        try:
            self.ollama_client.list()
        except Exception as e:
            print(f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
            print(f"Error details: {e}")
            sys.exit(1)

    def extract_and_validate_images(self, text: str):
        """Extrait et valide les chemins d'images"""

        # Pattern général pour chemins de fichiers
        pattern = r'(?:^|\s)([./~]?[^\s]*\.(?:jpg|jpeg|png|gif|bmp|webp))(?:\s|$)'

        potential_paths = re.findall(pattern, text, re.IGNORECASE)

        valid_images = []

        for path_str in potential_paths:
            path = Path(path_str).expanduser()  # Gère ~/

            # Vérifications
            if path.exists() and path.is_file():
                # Vérifier que c'est bien une image (optionnel)
                if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    valid_images.append(self.image_to_base64(str(path.absolute())))

        return valid_images


    def image_to_base64(self, image_path: str):
        """Convertit une image en base64"""
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded

    # Utilisation
    def chat(self, user_message: str) -> str:
        """Send a message and get response with tool support"""
        # Start timer
        # Add user message to history
        user_message = {
            "role": "user",
            "content": user_message
        }
        if self.image_mode:
            images_path = self.extract_and_validate_images(user_message["content"])
            user_message["images"] = images_path
            print(f"Image found: {images_path}")
            for image_path in images_path:
                user_message["content"] = user_message["content"].replace(image_path, "")
            print(f"Prompt: {user_message['content']}")

        self.conversation_history.append(user_message)
        self.start_time = time.time()
        self.elapsed = 0
        while True:
            # Call Ollama with conversation history and tools (with streaming)
            if not self.image_mode:
                stream = self.ollama_client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=self.tool_executor.tools_definition,
                    stream=True,
                    keep_alive="15m"  # Keep model in memory for 15 minutes
                )
            else:
                stream = self.ollama_client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                    stream=True,
                    keep_alive="15m"  # Keep model in memory for 15 minutes
                )
            # Collect the streamed response
            full_content = ""
            tool_calls = []
            console = Console()
            with Live(console=console, refresh_per_second=10, transient=True) as live:
                self.display_claudette_response(user_message["content"], live)
                for chunk in stream:
                    message = chunk.get("message", {})
                    if content := message.get("content"):
                        full_content += content
                        self.display_claudette_response(full_content, live)
                    elif message.get("tool_calls"):
                        tool_calls = message["tool_calls"]
                    else:
                        self.display_claudette_response(full_content, live)

            console.print(
                Group(
                    Text(f"(⏱️ {self.elapsed:.1f}s) Claudette: ", style="cyan"),
                    Markdown(full_content,  code_theme="dracula")
                )
            )

            print()  # Extra newline for spacing
            # Create the complete message for history
            assistant_message = {"role": "assistant", "content": full_content}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls

            # Add assistant response to history
            self.conversation_history.append(assistant_message)

            # Check if the model wants to use tools
            if not tool_calls:
                return full_content

            # Process tool calls
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                print(f"\n{Fore.MAGENTA}🔧 Using tool: {tool_name}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}Arguments: {json.dumps(tool_args, indent=2)}{Style.RESET_ALL}")
                # Execute the tool
                tool_result = self.tool_executor.execute_tool(tool_name, tool_args)

                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "tool",
                    "content": tool_result
                    })

                print(f"{Fore.YELLOW}Result: {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}{Style.RESET_ALL}")

            # Continue the loop to get the next response from the model

    def display_claudette_response(self, full_content: str, live: Live):
        self.elapsed = time.time() - self.start_time
        display_text = Text()
        display_text.append(f"(⏱️ {self.elapsed:.1f}s) ", style="cyan")
        display_text.append(f"Claudette: thinking... {len(full_content)}", style="dim cyan")
        live.update(display_text)

    def run(self):
        """Run the interactive chat loop"""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Claudette - Chat with Tools{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model: {self.model}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Host: {self.host}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Image mode: {self.image_mode}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"\nAvailable tools:")
        print(f"  • Web Search (DuckDuckGo)")
        print(f"  • Read File")
        print(f"  • Write File")
        print(f"  • Edit File")
        print(f"  • Execute Command")
        print(f"\nType 'quit' or 'exit' to end the conversation.")
        print(f"Type 'clear' to clear conversation history.")
        print(f"Type 'history' to view conversation history.\n")

        while True:
            try:
                session = PromptSession(history=FileHistory("claudette_history.txt"))
                user_input = session.prompt(HTML("<ansigreen>You: </ansigreen>")).strip()
                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit"]:
                    print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break

                if user_input.lower() == "clear":
                    self.conversation_history = []
                    print(f"\n{Fore.YELLOW}Conversation history cleared.{Style.RESET_ALL}")
                    continue

                if user_input.lower() == "history":
                    print(f"\n{Fore.YELLOW}Conversation History:{Style.RESET_ALL}")
                    for msg in self.conversation_history:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        print(f"\n{role.upper()}: {content[:200]}{'...' if len(str(content)) > 200 else ''}")
                    continue

                # Get response from the chatbot (response is already streamed to console)
                response = self.chat(user_input)

            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.RED}Please try again.{Style.RESET_ALL}")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default configuration
        return {
                "model": "llama3.1",
                "require_confirmation": True,
                "image_mode": False,
                "host": "http://192.168.1.138"
                }
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not load config.json: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Using default configuration.{Style.RESET_ALL}")
        return {
                "model": "llama3.1",
                "require_confirmation": True,
                "image_mode": False,
                "host": "http://192.168.1.138"
                }


def main():
    """Main entry point"""
    config = load_config()

    # Create and run the chatbot
    chatbot = ChatBot(
        host=config.get("host", "http://192.168.1.138"),
            model=config.get("model", "qwen3:30b"),
            image_mode=config.get("image_mode", False),
            require_confirmation=config.get("require_confirmation", True)
            )
    chatbot.run()


if __name__ == "__main__":
    main()
