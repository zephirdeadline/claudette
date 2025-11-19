#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
Main entry point
"""
import argparse
import sys
from typing import Any, Dict, Optional

import ollama
from colorama import Fore, Style

from src import ChatBot, ToolExecutor, ui
from src.models import Model, ModelFactory


def setup(
    model_name: Optional[str] = None, host: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup Claudette with optional parameters

    Args:
        model_name: Optional model name to use (default: qwen3:4b)
        host: Optional Ollama host URL (default: http://localhost:11434)

    Returns:
        Dictionary containing model, host, ollama_client, and ollama_models_available

    Raises:
        SystemExit: If cannot connect to Ollama
    """
    # Create tool executor
    tool_executor: ToolExecutor = ToolExecutor(require_confirmation=True)

    ollama_client: ollama.Client = ollama.Client(host=host)

    model: Optional[Model] = ModelFactory.create_model(
        model_name, ollama_client, tool_executor
    )

    try:
        ollama_models_available = ollama_client.list()
    except Exception as e:
        print(
            f"{Fore.RED}Error: Cannot connect to Ollama. Make sure it's running.{Style.RESET_ALL}"
        )
        print(f"Error details: {e}")
        sys.exit(1)

    return {
        "model": model,
        "host": host,
        "ollama_client": ollama_client,
        "ollama_models_available": ollama_models_available,
    }


if __name__ == "__main__":
    # Parse command line arguments
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Claudette - Chat with Ollama LLM with tool support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Use default configuration
  python main.py --model qwen2.5-coder:14b    # Use specific model
  python main.py --host http://localhost:11434 # Use specific Ollama host
  python main.py --model deepseek-r1:7b --host http://192.168.1.100:11434
        """,
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="qwen3-coder:30b",
        help="Model name to use (default: qwen3-coder:30b). Examples: qwen3:4b, deepseek-coder-v2:16b",
    )

    parser.add_argument(
        "--host",
        "-H",
        type=str,
        default="http://localhost:11434",
        help="Ollama host URL (default: http://localhost:11434)",
    )

    args: argparse.Namespace = parser.parse_args()

    # Setup with optional parameters
    settings: Dict[str, Any] = setup(model_name=args.model, host=args.host)

    if settings["model"] is None:
        print(
            f"{Fore.RED}Error: Failed to load model. Please check the model name and configuration.{Style.RESET_ALL}"
        )
        sys.exit(1)

    ui.show_welcome(
        settings["model"], settings["host"], settings["ollama_models_available"]
    )
    chatbot: ChatBot = ChatBot(settings["model"])
    chatbot.discuss()
