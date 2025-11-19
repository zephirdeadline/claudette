"""
Execute Command Tool - Execute a shell command
"""

import subprocess
from .base import Tool


class ExecuteCommandTool(Tool):
    """Execute a shell command and return the output"""

    def __init__(
        self, require_confirmation: bool = True, get_confirmation_callback=None
    ):
        """
        Initialize the execute command tool

        Args:
            require_confirmation: Whether to require user confirmation
            get_confirmation_callback: Callback function to get user confirmation
        """
        super().__init__(
            name="execute_command",
            description="Execute a shell command and return the output",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory for the command (optional)",
                    },
                },
                "required": ["command"],
            },
        )
        self.require_confirmation = require_confirmation
        self.get_confirmation_callback = get_confirmation_callback

    def execute(self, command: str, working_dir: str = None) -> str:
        """Execute a shell command"""
        # List of safe commands that don't require confirmation
        # These are read-only commands that don't modify the system
        safe_commands_prefixes = [
            # Navigation and exploration
            "ls ",
            "ls",
            "tree ",
            "tree",
            "pwd",
            "pwd ",
            "cd ",
            "cd",
            "find ",
            "find",
            "locate ",
            "locate",
            # File reading
            "cat ",
            "cat",
            "head ",
            "head",
            "tail ",
            "tail",
            "less ",
            "less",
            "more ",
            "more",
            "grep ",
            "grep",
            "wc ",
            "wc",
            "file ",
            "file",
            # System information
            "whoami",
            "whoami ",
            "hostname",
            "hostname ",
            "uname ",
            "uname",
            "date",
            "date ",
            "uptime",
            "uptime ",
            "df ",
            "df",
            "du ",
            "du",
            "free ",
            "free",
            "ps ",
            "ps",
            "top ",
            "top",
            "htop ",
            "htop",
            # Network (read-only)
            "ping ",
            "ping",
            "ifconfig ",
            "ifconfig",
            "ip ",
            "ip",
            "netstat ",
            "netstat",
            "curl ",
            "curl",
            "wget ",
            "wget",
            "nslookup ",
            "nslookup",
            "dig ",
            "dig",
            "host ",
            "host",
            # Comparison
            "diff ",
            "diff",
            "cmp ",
            "cmp",
            # Archive listing (read-only)
            "tar -t",
            "tar -tf",
            "tar -tvf",
            "unzip -l",
            "unzip -lv",
            "zip -sf",
            # Git (read-only)
            "git status",
            "git log",
            "git diff",
            "git branch",
            "git show",
            "git ls-files",
            "git ls-tree",
            "git reflog",
            "git remote",
            "git tag",
            # Development tools
            "which ",
            "which",
            "whereis ",
            "whereis",
            "type ",
            "type",
            "echo ",
            "echo",
            "env",
            "env ",
            "printenv",
            "printenv ",
        ]

        # Check if command is safe (no confirmation needed)
        is_safe_command = any(
            command.strip().startswith(prefix) for prefix in safe_commands_prefixes
        )

        # Only ask for confirmation if required AND command is not safe
        if (
            self.require_confirmation
            and self.get_confirmation_callback
            and not is_safe_command
        ):
            action = f"Command execution: {command}"
            if not self.get_confirmation_callback("⚠", action, []):
                return "Command execution cancelled by user."

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
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
