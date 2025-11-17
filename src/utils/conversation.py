"""
Conversation management utilities for Claudette
"""

import os
import yaml
from datetime import datetime
from .. import ui


def serialize_history(history: list) -> list:
    """
    Convert conversation history to JSON-serializable format

    Args:
        history: List of conversation messages

    Returns:
        Serialized conversation history
    """
    serialized = []
    for msg in history:
        serialized_msg = {}
        for key, value in msg.items():
            if key == "tool_calls":
                # Convert tool_calls objects to dictionaries
                serialized_msg[key] = [
                    {
                        "function": {
                            "name": tc.function.name if hasattr(tc.function, 'name') else tc["function"]["name"],
                            "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else tc["function"]["arguments"]
                        }
                    } if hasattr(tc, 'function') else tc
                    for tc in value
                ]
            elif key == "images":
                # Images are already serializable (list of paths)
                serialized_msg[key] = value
            else:
                # Copy other fields as-is
                serialized_msg[key] = value
        serialized.append(serialized_msg)
    return serialized


def save_conversation(conversation_history: list, filename: str = None) -> str | None:
    """
    Save conversation history to a file

    Args:
        conversation_history: List of conversation messages to save
        filename: Optional filename (without path). If None, generates timestamp-based name

    Returns:
        Full filepath if successful, None otherwise
    """
    # Create directory if it doesn't exist
    conversations_dir = ".claudette/conversations"
    os.makedirs(conversations_dir, exist_ok=True)

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.yaml"
    elif not filename.endswith('.yaml'):
        filename = f"{filename}.yaml"

    # Full path
    filepath = os.path.join(conversations_dir, filename)

    try:
        # Serialize history to YAML-compatible format
        serialized_history = serialize_history(conversation_history)

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(serialized_history, f, default_flow_style=False, allow_unicode=True)
        ui.show_save_confirmation(filepath)
        return filepath
    except Exception as e:
        ui.show_error(f"Failed to save conversation: {str(e)}")
        return None


def load_conversation(filename: str) -> list | None:
    """
    Load conversation history from a file

    Args:
        filename: Filename to load (with or without .yaml extension)

    Returns:
        Loaded conversation history as list, or None if failed
    """
    conversations_dir = ".claudette/conversations"

    # Add .yaml extension if not present
    if not filename.endswith('.yaml'):
        filename = f"{filename}.yaml"

    # Full path
    filepath = os.path.join(conversations_dir, filename)

    try:
        if not os.path.exists(filepath):
            ui.show_error(f"File not found: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_history = yaml.safe_load(f)

        ui.show_load_confirmation(filepath, len(loaded_history))
        return loaded_history
    except yaml.YAMLError:
        ui.show_error(f"Invalid YAML file: {filepath}")
        return None
    except Exception as e:
        ui.show_error(f"Failed to load conversation: {str(e)}")
        return None
