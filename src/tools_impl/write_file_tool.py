"""
Write File Tool - Write content to a file
"""

import os
from .base import Tool


class WriteFileTool(Tool):
    """Write content to a file (creates or overwrites)"""

    def __init__(
        self, require_confirmation: bool = True, get_confirmation_callback=None
    ):
        """
        Initialize the write file tool

        Args:
            require_confirmation: Whether to require user confirmation
            get_confirmation_callback: Callback function to get user confirmation
        """
        super().__init__(
            name="write_file",
            description="Write content to a file (creates or overwrites)",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        )
        self.require_confirmation = require_confirmation
        self.get_confirmation_callback = get_confirmation_callback

    def execute(self, file_path: str, content: str) -> str:
        """Write content to a file"""
        if self.require_confirmation and self.get_confirmation_callback:
            # Check if file exists to show appropriate message
            file_exists = os.path.exists(file_path)
            action = f"{'Overwrite' if file_exists else 'Create'} file: {file_path}"

            # Show content preview (first 100 chars)
            preview = content[:100] + "..." if len(content) > 100 else content

            if not self.get_confirmation_callback(
                "📝", action, [("Content", preview, "#6B7280")]
            ):
                return "File write cancelled by user."

        try:
            # Create directory if it doesn't exist
            os.makedirs(
                os.path.dirname(file_path) if os.path.dirname(file_path) else ".",
                exist_ok=True,
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully wrote to '{file_path}'."
        except PermissionError:
            return f"Error: Permission denied to write to '{file_path}'."
        except Exception as e:
            return f"Error writing file: {str(e)}"
