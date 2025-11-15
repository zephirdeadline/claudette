"""
UI and display utilities for Claudette
"""

import time
from typing import TYPE_CHECKING
from colorama import Fore, Style
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box

if TYPE_CHECKING:
    from .models import Model


def reset_timer(self):
    """Reset the elapsed time timer"""
    self.start_time = time.time()
    self.elapsed = 0

def show_welcome(model: "Model", host: str, models_available: list):
    """Display welcome message with configuration"""
    console = Console()

    # Title panel
    title = Text()
    title.append("✨ ", style="bold yellow")
    title.append("Claudette", style="bold cyan")
    title.append(" - AI Assistant with Tools", style="bold white")

    console.print(Panel(
        title,
        box=box.DOUBLE,
        border_style="cyan",
        padding=(1, 2)
    ))

    # Configuration table
    config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    config_table.add_column("Label", style="bold magenta", width=20)
    config_table.add_column("Value", style="cyan")

    config_table.add_row("🤖 Active Model", model.name)
    config_table.add_row("🌐 Host", host)
    config_table.add_row("🖼️  Image Mode", "✓ Enabled" if model.image_mode else "✗ Disabled")

    console.print(Panel(
        config_table,
        title="[bold white]⚙️  Configuration[/bold white]",
        border_style="blue",
        box=box.ROUNDED
    ))

    # Models available table
    models_table = Table(show_header=True, box=box.SIMPLE, padding=(0, 2))
    models_table.add_column("#", style="dim", width=4)
    models_table.add_column("Model Name", style="bold cyan")
    models_table.add_column("Size", style="green", justify="right")

    for idx, model_info in enumerate(models_available.models, 1):
        model_name = model_info.model
        # Extract size if available in the model name
        size = model_info.details.parameter_size if hasattr(model_info, 'details') else "N/A"
        models_table.add_row(str(idx), model_name, size)

    console.print(Panel(
        models_table,
        title=f"[bold white]📦 Available Models ({len(models_available.models)})[/bold white]",
        border_style="magenta",
        box=box.ROUNDED
    ))

    # Tools table
    tools_table = Table(show_header=False, box=None, padding=(0, 1))
    tools_table.add_column("Icon", style="bold yellow", width=4)
    tools_table.add_column("Tool", style="bold green", width=20)
    tools_table.add_column("Description", style="dim white")

    tools_table.add_row("🔍", "Web Search", "Search internet via DuckDuckGo")
    tools_table.add_row("📖", "Read File", "Read file contents")
    tools_table.add_row("✏️ ", "Write File", "Create or overwrite files")
    tools_table.add_row("📝", "Edit File", "Modify existing files")
    tools_table.add_row("⚡", "Execute Command", "Run shell commands")

    console.print(Panel(
        tools_table,
        title="[bold white]🛠️  Available Tools[/bold white]",
        border_style="green",
        box=box.ROUNDED
    ))

    # Commands help
    help_text = Text()
    help_text.append("💬 Commands: ", style="bold yellow")
    help_text.append("quit/exit", style="bold red")
    help_text.append(" • ", style="dim")
    help_text.append("clear", style="bold blue")
    help_text.append(" • ", style="dim")
    help_text.append("history", style="bold magenta")

    console.print(Panel(
        help_text,
        border_style="dim white",
        box=box.ROUNDED,
        padding=(0, 2)
    ))
    console.print()

def show_thinking(full_content: str, live: Live, start_time: float):
    """Display thinking indicator while processing"""
    elapsed = time.time() - start_time

    # Create animated thinking indicator
    dots = "." * (int(elapsed * 2) % 4)
    thinking_text = Text()
    thinking_text.append("🤔 ", style="bold yellow")
    thinking_text.append("Claudette ", style="bold cyan")
    thinking_text.append("is thinking", style="dim white")
    thinking_text.append(dots.ljust(3), style="dim white")
    thinking_text.append(f"  ⏱️  {elapsed:.1f}s", style="dim magenta")

    if len(full_content) > 0:
        thinking_text.append(f" • {len(full_content)} chars", style="dim blue")

    live.update(thinking_text)

def show_response(console: Console, elapsed: float, content: str):
    """Display the final response with markdown formatting"""
    # Header with timing
    header = Text()
    header.append("✨ ", style="bold yellow")
    header.append("Claudette", style="bold cyan")
    header.append(f"  ⏱️  {elapsed:.1f}s", style="dim magenta")

    console.print(Panel(
        Group(
            header,
            Text(""),  # Empty line
            Markdown(content, code_theme="monokai")
        ),
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    console.print()  # Extra newline for spacing

def show_tool_usage(tool_name: str, tool_args: dict):
    """Display tool usage information"""
    import json
    console = Console()

    # Tool icon mapping
    tool_icons = {
        "web_search": "🔍",
        "read_file": "📖",
        "write_file": "✏️",
        "edit_file": "📝",
        "execute_command": "⚡"
    }

    icon = tool_icons.get(tool_name, "🔧")

    # Create tool info panel
    tool_info = Text()
    tool_info.append(f"{icon} ", style="bold yellow")
    tool_info.append(tool_name.replace("_", " ").title(), style="bold magenta")

    # Format arguments
    args_text = json.dumps(tool_args, indent=2)

    console.print(Panel(
        Group(
            tool_info,
            Text(""),
            Text("Arguments:", style="bold white"),
            Text(args_text, style="dim cyan")
        ),
        title="[bold white]🛠️  Tool Execution[/bold white]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2)
    ))

def show_tool_result(result: str):
    """Display tool execution result"""
    console = Console()
    truncated = result[:500] + ('\n...[truncated]' if len(result) > 500 else '')

    console.print(Panel(
        Text(truncated, style="green"),
        title="[bold white]✅ Tool Result[/bold white]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    console.print()

def show_history(conversation_history: list):
    """Display conversation history"""
    console = Console()

    history_table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        padding=(0, 2)
    )
    history_table.add_column("#", style="dim", width=4)
    history_table.add_column("Role", style="bold", width=12)
    history_table.add_column("Content", style="white")

    role_icons = {
        "user": "👤",
        "assistant": "🤖",
        "system": "⚙️",
        "tool": "🔧"
    }

    for idx, msg in enumerate(conversation_history, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        truncated = str(content)[:150] + ('...' if len(str(content)) > 150 else '')

        icon = role_icons.get(role, "❓")
        role_display = f"{icon} {role.capitalize()}"

        role_style = {
            "user": "green",
            "assistant": "cyan",
            "system": "yellow",
            "tool": "magenta"
        }.get(role, "white")

        history_table.add_row(
            str(idx),
            role_display,
            truncated,
            style=role_style
        )

    console.print(Panel(
        history_table,
        title="[bold white]📜 Conversation History[/bold white]",
        border_style="yellow",
        box=box.DOUBLE
    ))
    console.print()

def show_error(error_msg: str):
    """Display error message"""
    console = Console()
    error_text = Text()
    error_text.append("❌ ", style="bold red")
    error_text.append("Error\n\n", style="bold red")
    error_text.append(error_msg, style="red")
    error_text.append("\n\nPlease try again.", style="dim red")

    console.print(Panel(
        error_text,
        border_style="red",
        box=box.HEAVY,
        padding=(1, 2)
    ))
    console.print()

def show_clear_confirmation():
    """Display confirmation that history was cleared"""
    console = Console()
    console.print(Panel(
        Text("✓ Conversation history cleared", style="bold green"),
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 2)
    ))
    console.print()

def show_goodbye():
    """Display goodbye message"""
    console = Console()
    goodbye_text = Text()
    goodbye_text.append("👋 ", style="bold yellow")
    goodbye_text.append("Goodbye! ", style="bold cyan")
    goodbye_text.append("See you next time!", style="dim white")

    console.print(Panel(
        goodbye_text,
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    ))

def show_image_found(image_paths: list, prompt: str):
    """Display information about found images"""
    console = Console()

    image_info = Text()
    image_info.append("🖼️  Images detected\n\n", style="bold magenta")
    image_info.append(f"Count: {len(image_paths)}\n", style="cyan")
    image_info.append("Paths:\n", style="bold white")
    for path in image_paths:
        image_info.append(f"  • {path}\n", style="dim cyan")

    console.print(Panel(
        image_info,
        title="[bold white]Image Processing[/bold white]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2)
    ))
    console.print()
