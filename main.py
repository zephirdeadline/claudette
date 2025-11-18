#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
Main entry point
"""
import argparse
import ollama
import sys
from colorama import Fore, Style

from src import ChatBot, ToolExecutor, ui
from src.models import ModelFactory


def setup(model_name=None, host=None):
    """
    Setup Claudette with optional parameters

    Args:
        model_name: Optional model name to use (default: qwen3:4b)
        host: Optional Ollama host URL (default: http://localhost:11434)
    """
    # Create tool executor
    tool_executor = ToolExecutor(require_confirmation=True)

    ollama_client = ollama.Client(host=host)

    model = ModelFactory.create_model(model_name, ollama_client, tool_executor)

    try:
        ollama_models_available = ollama_client.list()
    except Exception as e:
        print(f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
        print(f"Error details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}")
        print(f"Error details: {e}")
        sys.exit(1)
    return {
        "model": model,
        "host": host,
        "ollama_client": ollama_client,
        "ollama_models_available": ollama_models_available
    }
    # Create and run the chatbot



if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Claudette - Chat with Ollama LLM with tool support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Use default configuration
  python main.py --model qwen2.5-coder:14b    # Use specific model
  python main.py --host http://localhost:11434 # Use specific Ollama host
  python main.py --model deepseek-r1:7b --host http://192.168.1.100:11434
        """
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="qwen3-coder:30b",
        help=f"Model name to use (default: qwen3-coder:30b). Examples: qwen3:4b, deepseek-coder-v2:16b"
    )

    parser.add_argument(
        "--host", "-H",
        type=str,
        default="http://localhost:11434",
        help=f"Ollama host URL (default: http://localhost:11434. Example: http://localhost:11434"
    )

    args = parser.parse_args()

    # Setup with optional parameters
    settings = setup(model_name=args.model, host=args.host)

    if settings["model"] is None:
        print(f"{Fore.RED}Error: Failed to load model. Please check the model name and configuration.{Style.RESET_ALL}")
        sys.exit(1)

    ui.show_welcome(settings["model"], settings["host"], settings["ollama_models_available"])
    chatbot = ChatBot(settings["model"])
    chatbot.discuss()
