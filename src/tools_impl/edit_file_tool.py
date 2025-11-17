"""
Edit File Tool - Edit a file by replacing specific content
"""

import difflib
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from .base import Tool


class EditFileTool(Tool):
    """Edit a file by replacing specific content"""

    def __init__(self, require_confirmation: bool = True):
        """
        Initialize the edit file tool

        Args:
            require_confirmation: Whether to require user confirmation
        """
        super().__init__(
            name="edit_file",
            description="Edit a file by replacing specific content",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "Content to replace (must match exactly)"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content to insert"
                    }
                },
                "required": ["file_path", "old_content", "new_content"]
            }
        )
        self.require_confirmation = require_confirmation

    def _generate_diff(self, old_text: str, new_text: str, file_path: str) -> str:
        """Generate a unified diff between old and new text"""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )

        return ''.join(diff)

    def execute(self, file_path: str, old_content: str, new_content: str) -> str:
        """Edit a file by replacing content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_content not in content:
                return f"Error: Could not find the specified content in '{file_path}'."

            new_file_content = content.replace(old_content, new_content, 1)

            # Generate diff for display
            diff_output = self._generate_diff(content, new_file_content, file_path)

            if self.require_confirmation:
                console = Console()
                console.print()

                # Show action header
                header_text = Text()
                header_text.append("  ✏️ ", style="bold #F59E0B")
                header_text.append(f"Edit file: {file_path}", style="bold #E5E7EB")
                console.print(header_text)
                console.print()

                # Display diff with syntax highlighting
                if diff_output:
                    syntax = Syntax(diff_output, "diff", theme="monokai", line_numbers=False)
                    console.print(Panel(syntax, border_style="#F59E0B", padding=(0, 1)))
                else:
                    console.print("  [dim]No differences detected[/dim]")

                console.print()

                # Get confirmation
                session = PromptSession()
                confirmation = session.prompt(HTML('<ansi color="#9CA3AF">    Allow? (Y/n): </ansi>')).strip().lower()

                if confirmation not in ['', 'y', 'yes']:
                    return "File edit cancelled by user."

            # Write the new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)

            # Return success with diff
            return f"Successfully edited '{file_path}'.\n\nChanges:\n{diff_output}"
        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except Exception as e:
            return f"Error editing file: {str(e)}"
