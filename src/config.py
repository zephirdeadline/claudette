"""
Configuration management for Claudette
"""

from typing import Any, Dict

import yaml
from colorama import Fore, Style

# Default configuration constants
DEFAULT_CONFIG: Dict[str, Any] = {
    "model": "llama3.1",
    "require_confirmation": True,
    "image_mode": False,
    "host": "http://localhost",
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml

    Returns:
        Configuration dictionary with model, require_confirmation, image_mode, and host

    Note:
        Returns default configuration if config.yaml is not found or cannot be loaded
    """
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if config else DEFAULT_CONFIG.copy()
    except FileNotFoundError:
        # Return default configuration
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not load config.yaml: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Using default configuration.{Style.RESET_ALL}")
        return DEFAULT_CONFIG.copy()
