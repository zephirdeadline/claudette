#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
"""

import json
import sys
import time
import threading
from typing import List, Dict, Any
import ollama
from colorama import Fore, Style, init
from tools import ToolExecutor
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory 
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text

# Initialize colorama for colored output
init(autoreset=True)


class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, model: str = "llama3.1", require_confirmation: bool = True):
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
        self.ollama_client = ollama.Client(host='http://192.168.1.138')
        self.timer_running = False
        self.timer_text = ""
        self.timer_print = True
        # Check if Ollama is available
        try:
            self.ollama_client.list()
        except Exception as e:
            print(f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
            print(f"Error details: {e}")
            sys.exit(1)

    def _display_timer(self, start_time):
        """Display elapsed time dynamically in a separate thread"""
        while self.timer_running:
            elapsed = time.time() - start_time
            # Print timer on the same line (carriage return)
            self.timer_text = f"(⏱️ {elapsed:.1f}s)"
            # if self.timer_print:
            #     print(f"{Fore.CYAN}{self.timer_text}{Style.RESET_ALL}", end="", flush=True)

            time.sleep(0.1)  # Update every 100ms


    def chat(self, user_message: str) -> str:
        """Send a message and get response with tool support"""
        # Start timer
        self.start_time = time.time()
        self.timer_running = True
        timer_thread = threading.Thread(target=self._display_timer, args=(time.time(),), daemon=True)
        timer_thread.start()
        #timer_started = True

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
            })

        while True:
            # Call Ollama with conversation history and tools (with streaming)
            stream = self.ollama_client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=self.tool_executor.tools_definition,
                    stream=True,
                    keep_alive="15m"  # Keep model in memory for 15 minutes
                    )
            # Collect the streamed response
            full_content = ""
            tool_calls = []
            console = Console()
            with Live(console=console, refresh_per_second=20) as live:
                for chunk in stream:

                    message = chunk.get("message", {})

                    # Stream content if available
                    if message.get("content"):
                        self.timer_running = False
                        timer_thread.join()
                        content = message["content"]
                        full_content += content

                    # Collect tool calls if present
                    if message.get("tool_calls"):
                        self.timer_running = False
                        timer_thread.join()
                        tool_calls = message["tool_calls"]

                    # Combine timer, label and content on the same line
                    display_text = Text()
                    display_text.append(self.timer_text + " ", style="cyan")
                    display_text.append("Claudette: ", style="cyan")
                    md = Markdown(full_content, code_theme="dracula")
                    live.update(Group(display_text, md))

            #self.timer_print = True
            print()
            # Create the complete message for history
            assistant_message = {"role": "assistant", "content": full_content}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls

            # Add assistant response to history
            self.conversation_history.append(assistant_message)

            # Check if the model wants to use tools
            if not tool_calls:
                # No tool calls, display final elapsed time and return
                elapsed_time = time.time() - self.start_time
                #print(f"\n{Fore.BLUE}⏱️  Total response time: {elapsed_time:.2f}s{Style.RESET_ALL}")
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

    def run(self):
        """Run the interactive chat loop"""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Claudette - Chat with Tools{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Model: {self.model}{Style.RESET_ALL}")
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
                print(f"{Fore.GREEN}You: {Style.RESET_ALL}", end="")
                user_input = session.prompt().strip()
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
                "require_confirmation": True
                }
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not load config.json: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Using default configuration.{Style.RESET_ALL}")
        return {
                "model": "llama3.1",
                "require_confirmation": True
                }


def main():
    """Main entry point"""
    config = load_config()

    # Create and run the chatbot
    chatbot = ChatBot(
            model=config.get("model", "llama3.1"),
            require_confirmation=config.get("require_confirmation", True)
            )

    chatbot.run()


if __name__ == "__main__":
    main()
