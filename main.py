#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
"""

import json
import sys
from typing import List, Dict, Any
import ollama
from colorama import Fore, Style, init
from tools import ToolExecutor

# Initialize colorama for colored output
init(autoreset=True)


class ChatBot:
    """Main chatbot class with Ollama integration"""

    def __init__(self, model: str = "llama3.1", require_confirmation: bool = True):
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_executor = ToolExecutor(require_confirmation=require_confirmation)

        # Check if Ollama is available
        try:
            ollama.list()
        except Exception as e:
            print(f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
            print(f"Error details: {e}")
            sys.exit(1)

    def print_message(self, role: str, content: str):
        """Print a formatted message"""
        if role == "user":
            print(f"\n{Fore.GREEN}You: {Style.RESET_ALL}{content}")
        elif role == "assistant":
            print(f"\n{Fore.CYAN}Assistant: {Style.RESET_ALL}{content}")
        elif role == "tool":
            print(f"\n{Fore.YELLOW}Tool Result: {Style.RESET_ALL}{content}")

    def chat(self, user_message: str) -> str:
        """Send a message and get response with tool support"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        while True:
            # Call Ollama with conversation history and tools
            response = ollama.chat(
                model=self.model,
                messages=self.conversation_history,
                tools=self.tool_executor.tools_definition
            )

            # Add assistant response to history
            self.conversation_history.append(response["message"])

            # Check if the model wants to use tools
            if not response["message"].get("tool_calls"):
                # No tool calls, return the final response
                return response["message"]["content"]

            # Process tool calls
            for tool_call in response["message"]["tool_calls"]:
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

                print(f"{Fore.YELLOW}Result: {tool_result[:]}{'...' if len(tool_result) > 200 else ''}{Style.RESET_ALL}")

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
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()

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

                # Get response from the chatbot
                response = self.chat(user_input)

                # Print the response
                self.print_message("assistant", response)

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
