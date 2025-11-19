"""
Claudette - Chat with Ollama LLM with tool support
"""

from .chatbot import ChatBot
from .tools import ToolExecutor
from .image_utils import extract_and_validate_images, image_to_base64

__all__ = ["ChatBot", "ToolExecutor", "extract_and_validate_images", "image_to_base64"]
