"""
CD command - Change working directory
"""

import os
from pathlib import Path
from .base import Command
from .. import ui


class CdCommand(Command):
    """Change the current working directory"""

    def __init__(self):
        super().__init__(
            name="cd",
            description="Change working directory",
            usage="/cd <directory>",
        )

    def execute(self, chatbot, args):
        if not args:
            # If no argument, go to home directory
            target_dir = str(Path.home())
        else:
            target_dir = " ".join(args)  # Join all args in case of spaces

        try:
            # Expand user path (e.g., ~)
            target_dir = os.path.expanduser(target_dir)

            # Convert to absolute path if relative
            if not os.path.isabs(target_dir):
                target_dir = os.path.abspath(target_dir)

            # Check if directory exists
            if not os.path.exists(target_dir):
                ui.show_error(f"Directory not found: {target_dir}")
                return None

            if not os.path.isdir(target_dir):
                ui.show_error(f"Not a directory: {target_dir}")
                return None

            # Change directory
            os.chdir(target_dir)
            ui.show_info(f"Changed directory to: {os.getcwd()}")

        except PermissionError:
            ui.show_error(f"Permission denied: {target_dir}")
        except Exception as e:
            ui.show_error(f"Failed to change directory: {e}")

        return None