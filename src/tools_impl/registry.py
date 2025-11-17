"""
Tool Registry - Manages all available tools
"""

from typing import Dict, List, Any

from .base import Tool
from .ask_user_tool import AskUserTool
from .web_search_tool import WebSearchTool
from .read_file_tool import ReadFileTool
from .write_file_tool import WriteFileTool
from .edit_file_tool import EditFileTool
from .execute_command_tool import ExecuteCommandTool
from .get_time_tool import GetCurrentTimeTool
from .list_directory_tool import ListDirectoryTool


class ToolRegistry:
    """Registry for managing all available tools"""

    def __init__(self, require_confirmation: bool = True, get_confirmation_callback=None):
        """
        Initialize the tool registry

        Args:
            require_confirmation: Whether tools should require user confirmation
            get_confirmation_callback: Callback function for getting user confirmation
        """
        self.require_confirmation = require_confirmation
        self.get_confirmation_callback = get_confirmation_callback
        self.tools: Dict[str, Tool] = {}
        self._register_tools()

    def _register_tools(self):
        """Register all available tools"""
        tools = [
            AskUserTool(),
            WebSearchTool(),
            ReadFileTool(),
            WriteFileTool(
                require_confirmation=self.require_confirmation,
                get_confirmation_callback=self.get_confirmation_callback
            ),
            EditFileTool(require_confirmation=self.require_confirmation),
            ExecuteCommandTool(
                require_confirmation=self.require_confirmation,
                get_confirmation_callback=self.get_confirmation_callback
            ),
            GetCurrentTimeTool(),
            ListDirectoryTool(),
        ]

        for tool in tools:
            self.tools[tool.name] = tool

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM function calling

        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return [tool.get_definition() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool by name with given arguments

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool

        Returns:
            String result of the tool execution
        """
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        tool = self.tools[tool_name]

        try:
            return tool.execute(**arguments)
        except TypeError as e:
            return f"Error: Invalid arguments for {tool_name}: {str(e)}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name"""
        return self.tools.get(name)
