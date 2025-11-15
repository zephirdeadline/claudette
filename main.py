#!/usr/bin/env python3
"""
Claudette - Chat with Ollama LLM with tool support
Main entry point
"""
import ollama
import sys
from colorama import Fore, Style

from src import ChatBot, ToolExecutor, load_config, ui
from src.models import Model, DeepseekCodeV2, Qwen3_4b


def setup():
    """Main entry point"""
    config = load_config()

    # Create tool executor
    tool_executor = ToolExecutor(
        require_confirmation=config.get("require_confirmation", True)
    )
    host = config.get("host", "http://192.168.1.138")
    ollama_client = ollama.Client(host=host)

    model_name = config.get("model", "qwen3:30b")
    model = Model(name=model_name, system_prompt="Hello", ollama_client=ollama_client, image_mode=False, tool_executor=tool_executor)
    model = DeepseekCodeV2(model_name, ollama_client)
    model = Qwen3_4b(ollama_client, tool_executor)
    try:
        models_available = ollama_client.list()
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
        "models_available": models_available
    }
    # Create and run the chatbot



if __name__ == "__main__":
    settings = setup()
    ui.show_welcome(settings["model"], settings["host"], settings["models_available"])
    chatbot = ChatBot(settings["model"], settings["ollama_client"])
    chatbot.discuss()
