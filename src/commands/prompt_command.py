"""
Prompt command - Display system prompt
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box
from .base import Command
from .. import ui


class PromptCommand(Command):
    """Display the current system prompt"""

    def __init__(self):
        super().__init__(
            name="prompt",
            description="Display the current system prompt",
            usage="/prompt",
        )

    def execute(self, chatbot, args):
        console = Console()
        console.print()

        # Get the system prompt from the model
        system_prompt = chatbot.model.system_prompt

        if not system_prompt:
            ui.show_error("No system prompt configured for this model")
            return None

        # Display the system prompt in a nice panel
        console.print(
            Panel(
                Markdown(system_prompt, code_theme="monokai"),
                title=f"[bold]System Prompt - {chatbot.model.name}[/bold]",
                border_style="dim #9CA3AF",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

        # Show prompt statistics
        from .. import ui as ui_module

        token_count = ui_module.get_token_count(system_prompt)
        char_count = len(system_prompt)
        lines_count = system_prompt.count("\n") + 1

        stats_text = console.print(
            f"  [dim #9CA3AF]📊 Statistics:[/dim #9CA3AF] "
            f"[#E5E7EB]{token_count} tokens[/#E5E7EB] · "
            f"[#E5E7EB]{char_count} characters[/#E5E7EB] · "
            f"[#E5E7EB]{lines_count} lines[/#E5E7EB]"
        )
        console.print()

        return None
