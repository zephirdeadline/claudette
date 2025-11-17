"""
Read File Tool - Read the contents of a file
"""

from .base import Tool


class ReadFileTool(Tool):
    """Read the contents of a file"""

    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        )

    def execute(self, file_path: str) -> str:
        """Read and return file contents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File content of {file_path}:\n\n{content}"
        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except PermissionError:
            return f"Error: Permission denied to read '{file_path}'."
        except Exception as e:
            return f"Error reading file: {str(e)}"
