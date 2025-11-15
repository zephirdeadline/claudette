"""
Claudette - Chat with Ollama LLM with tool support
"""

from .chatbot import ChatBot
from .config import load_config, get_system_prompt
from .tools import ToolExecutor
from .image_utils import extract_and_validate_images, image_to_base64

__all__ = [
    'ChatBot',
    'load_config',
    'get_system_prompt',
    'ToolExecutor',
    'extract_and_validate_images',
    'image_to_base64'
]
