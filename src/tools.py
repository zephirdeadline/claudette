"""
Tools implementation for LLM function calling
"""

import os
import subprocess
import json
from typing import Any, Dict, List
from ddgs import DDGS


class ToolExecutor:
    """Execute tools requested by the LLM"""

    def __init__(self, require_confirmation: bool = True):
        self.require_confirmation = require_confirmation
        self.tools_definition = self._define_tools()

    def _get_confirmation(self, emoji: str, action: str, details: List[tuple]) -> bool:
        """
        Show a confirmation prompt and get user response.

        Args:
            emoji: Emoji to display (e.g., "⚠", "📝", "✏️")
            action: Action description (e.g., "Command execution", "Create file")
            details: List of (label, value, style) tuples to display

        Returns:
            True if user confirms, False otherwise
        """
        from rich.console import Console
        from rich.text import Text

        console = Console()
        console.print()

        # Show action header
        warning_text = Text()
        warning_text.append(f"  {emoji} ", style="bold #F59E0B")
        warning_text.append(f"{action}", style="bold #E5E7EB")
        console.print(warning_text)

        # Show details
        for label, value, style in details:
            detail_text = Text()
            detail_text.append(f"    {label}: ", style=style)
            detail_text.append(value, style="#9CA3AF")
            console.print(detail_text)

        confirmation = input("    Allow? (Y/n): ").strip().lower()
        # Default to 'yes' if user just presses Enter
        return confirmation in ['', 'y', 'yes']

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available tools for the LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the internet for information using DuckDuckGo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file (creates or overwrites)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing specific content",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "Execute a shell command and return the output",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute"
                            },
                            "working_dir": {
                                "type": "string",
                                "description": "Working directory for the command (optional)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    def web_search(self, query: str, max_results: int = 5) -> str:
        """Search the web using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                # Try Instant Answers first (for queries like "current date", "2+2", etc.)
                try:
                    instant_answers = list(ddgs.answers(query))
                    if instant_answers:
                        formatted_answers = []
                        for answer in instant_answers:
                            # Format the instant answer
                            text = answer.get('text', '')
                            url = answer.get('url', '')
                            if text:
                                formatted_answers.append(f"Instant Answer: {text}")
                                if url:
                                    formatted_answers.append(f"Source: {url}")

                        if formatted_answers:
                            return "\n".join(formatted_answers)
                except Exception:
                    # If instant answers fail, continue to regular search
                    pass

                # Fall back to regular web search
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return "No results found."

            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. {result['title']}\n"
                    f"   URL: {result['href']}\n"
                    f"   {result['body']}\n"
                )

            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error performing web search: {str(e)}"

    def read_file(self, file_path: str) -> str:
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

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file"""
        if self.require_confirmation:
            # Check if file exists to show appropriate message
            file_exists = os.path.exists(file_path)
            action = f"{'Overwrite' if file_exists else 'Create'} file: {file_path}"

            # Show content preview (first 100 chars)
            preview = content[:100] + "..." if len(content) > 100 else content

            if not self._get_confirmation("📝", action, [("Content", preview, "#6B7280")]):
                return "File write cancelled by user."

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully wrote to '{file_path}'."
        except PermissionError:
            return f"Error: Permission denied to write to '{file_path}'."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def edit_file(self, file_path: str, old_content: str, new_content: str) -> str:
        """Edit a file by replacing content"""
        if self.require_confirmation:
            # Show what's being replaced (preview)
            old_preview = old_content[:80] + "..." if len(old_content) > 80 else old_content
            new_preview = new_content[:80] + "..." if len(new_content) > 80 else new_content

            action = f"Edit file: {file_path}"
            details = [
                ("Replace", old_preview, "#EF4444"),
                ("With", new_preview, "#10B981")
            ]

            if not self._get_confirmation("✏️", action, details):
                return "File edit cancelled by user."

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_content not in content:
                return f"Error: Could not find the specified content in '{file_path}'."

            new_file_content = content.replace(old_content, new_content, 1)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)

            return f"Successfully edited '{file_path}'."
        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def execute_command(self, command: str, working_dir: str = None) -> str:
        """Execute a shell command"""
        if self.require_confirmation:
            action = f"Command execution: {command}"
            if not self._get_confirmation("⚠", action, []):
                return "Command execution cancelled by user."

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            output.append(f"Return code: {result.returncode}")

            return "\n".join(output)
        except subprocess.TimeoutExpired:
            return "Error: Command execution timed out (30s limit)."
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name with given arguments"""
        tool_methods = {
            "web_search": self.web_search,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "edit_file": self.edit_file,
            "execute_command": self.execute_command
        }

        if tool_name not in tool_methods:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            return tool_methods[tool_name](**arguments)
        except TypeError as e:
            return f"Error: Invalid arguments for {tool_name}: {str(e)}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
