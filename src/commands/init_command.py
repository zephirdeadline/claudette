"""
Init command - Generate AGENTS.md file
"""

from rich.console import Console
from rich.live import Live
from .base import Command
from .. import ui


class InitCommand(Command):
    """Generate AGENTS.md file with comprehensive project documentation"""

    def __init__(self):
        super().__init__(
            name="init",
            description="Generate AGENTS.md file with project documentation",
            usage="/init",
        )

    def execute(self, chatbot, args):
        console = Console()

        # Show start message
        ui.show_info("🚀 Starting project analysis for AGENTS.md generation...")
        console.print()

        # Create the analysis prompt (ultra-direct with concrete examples)
        analysis_prompt = """⚠️ MANDATORY ACTION REQUIRED ⚠️

DO NOT ANALYZE. DO NOT EXPLAIN. EXECUTE THESE TOOLS NOW:

1. execute_command: {"command": "find . -type f -name '*.py' | head -30"}
2. read_file: {"file_path": "./README.md"}
3. read_file: {"file_path": "./main.py"}
4. read_file: {"file_path": "./requirements.txt"}
5. write_file: {"file_path": "./AGENTS.md", "content": "[YOUR CONTENT]"}

THE FILE AGENTS.md MUST CONTAIN:
```
# Project: [name from README or main.py]

## Overview
[1-2 sentences from README]

## Structure
[paste output from find command]

## Tech Stack
- Python
- [libraries from requirements.txt]

## Entry Point
main.py

## Functions Map
[For EACH .py file found: list all functions/classes with line numbers]
```

⚠️ WARNING: If you respond with explanations instead of using tools, you FAILED the task.
⚠️ SUCCESS = AGENTS.md file exists on disk after you finish
⚠️ FAILURE = No file created

START EXECUTING TOOLS IMMEDIATELY."""

        try:
            # Create a temporary conversation with the analysis prompt
            temp_history = [chatbot.model.get_system_prompt()]
            temp_message = chatbot.model.get_user_message(analysis_prompt)
            temp_history.append(temp_message)

            # Process the analysis with live display
            with Live(console=console, refresh_per_second=10, transient=False) as live:
                response, elapsed, thinking_content = chatbot.model.process_message(
                    temp_history,
                    live,
                    temperature=0.7,  # Higher temperature for tool usage initiative
                    enable_thinking=chatbot.enable_thinking,
                )

            # Show completion
            console.print()
            ui.show_success("✅ AGENTS.md file generation completed!")
            console.print()
            ui.show_response(console, elapsed, response, thinking_content)

        except Exception as e:
            ui.show_error(f"Failed to generate AGENTS.md: {str(e)}")

        return None
