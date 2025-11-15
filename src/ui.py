"""
UI and display utilities for Claudette
"""

import time
from typing import TYPE_CHECKING
from colorama import Fore, Style
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text

if TYPE_CHECKING:
    from .models import Model


def reset_timer(self):
    """Reset the elapsed time timer"""
    self.start_time = time.time()
    self.elapsed = 0

def show_welcome(model: "Model", host: str, models_available: list):
    """Display welcome message with configuration"""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Claudette - Chat with Tools{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Model: {model.name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Models Available: {[ m.model for m in models_available.models]}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Host: {host}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Image mode: {model.image_mode}{Style.RESET_ALL}")
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

def show_thinking(full_content: str, live: Live, start_time: float):
    """Display thinking indicator while processing"""
    elapsed = time.time() - start_time
    display_text = Text()
    display_text.append(f"(⏱️ {elapsed:.1f}s) ", style="cyan")
    display_text.append(f"Claudette: thinking... {len(full_content)}", style="dim cyan")
    live.update(display_text)

def show_response(console: Console, elapsed: float, content: str):
    """Display the final response with markdown formatting"""
    console.print(
        Group(
            Text(f"(⏱️ {elapsed:.1f}s) Claudette: ", style="cyan"),
            Markdown(content, code_theme="dracula")
        )
    )  # Extra newline for spacing

def show_tool_usage(tool_name: str, tool_args: dict):
    """Display tool usage information"""
    import json
    print(f"\n{Fore.MAGENTA}🔧 Using tool: {tool_name}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Arguments: {json.dumps(tool_args, indent=2)}{Style.RESET_ALL}")

def show_tool_result(result: str):
    """Display tool execution result"""
    truncated = result[:200] + ('...' if len(result) > 200 else '')
    print(f"{Fore.YELLOW}Result: {truncated}{Style.RESET_ALL}")

def show_history(conversation_history: list):
    """Display conversation history"""
    print(f"\n{Fore.YELLOW}Conversation History:{Style.RESET_ALL}")
    for msg in conversation_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        truncated = str(content)[:200] + ('...' if len(str(content)) > 200 else '')
        print(f"\n{role.upper()}: {truncated}")

def show_error(error_msg: str):
    """Display error message"""
    print(f"\n{Fore.RED}Error: {error_msg}{Style.RESET_ALL}")
    print(f"{Fore.RED}Please try again.{Style.RESET_ALL}")

def show_clear_confirmation():
    """Display confirmation that history was cleared"""
    print(f"\n{Fore.YELLOW}Conversation history cleared.{Style.RESET_ALL}")

def show_goodbye():
    """Display goodbye message"""
    print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")

def show_image_found(image_paths: list, prompt: str):
    """Display information about found images"""
    print(f"Image found: {image_paths}")
    print(f"Prompt: {prompt}")
