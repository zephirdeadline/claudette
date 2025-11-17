"""
Configuration management for Claudette
"""

import yaml
from typing import Dict, Any
from colorama import Fore, Style


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return default configuration
        return {
            "model": "llama3.1",
            "require_confirmation": True,
            "image_mode": False,
            "host": "http://192.168.1.138"
        }
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not load config.yaml: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Using default configuration.{Style.RESET_ALL}")
        return {
            "model": "llama3.1",
            "require_confirmation": True,
            "image_mode": False,
            "host": "http://192.168.1.138"
        }
