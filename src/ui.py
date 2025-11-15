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
from rich.align import Align

if TYPE_CHECKING:
    from .models import Model

# Professional color scheme
BRAND_COLOR = "#7C3AED"  # Purple
ACCENT_COLOR = "#10B981"  # Green
TEXT_PRIMARY = "#E5E7EB"  # Light gray
TEXT_SECONDARY = "#9CA3AF"  # Medium gray
SUCCESS_COLOR = "#10B981"  # Green
WARNING_COLOR = "#F59E0B"  # Amber



def show_welcome(model: "Model", host: str, models_available: list):
    """Display welcome message with configuration"""
    console = Console()

    # Minimalist header
    console.print()
    header = Text()
    header.append("claudette", style=f"bold {BRAND_COLOR}")
    header.append(" ", style="")
    header.append("v1.0", style=f"dim {TEXT_SECONDARY}")
    console.print(Align.center(header))

    subtitle = Text("AI Assistant with Local LLM", style=f"dim {TEXT_SECONDARY}")
    console.print(Align.center(subtitle))
    console.print()

    # Clean info grid
    info_grid = Table.grid(padding=(0, 2))
    info_grid.add_column(style=f"{TEXT_SECONDARY}", justify="right", width=15)
    info_grid.add_column(style=f"bold {TEXT_PRIMARY}")

    info_grid.add_row("MODEL", model.name)
    info_grid.add_row("HOST", host)
    info_grid.add_row("VISION", "enabled" if model.image_mode else "disabled")

    console.print(Panel(
        Align.center(info_grid),
        box=box.ROUNDED,
        border_style=f"dim {TEXT_SECONDARY}",
        padding=(1, 4)
    ))

    # Available models - complete list with aligned table
    if len(models_available.models) > 0:
        models_header = Text()
        models_header.append(f"MODELS ({len(models_available.models)})", style=f"bold {TEXT_SECONDARY}")
        console.print(Align.center(models_header))
        console.print()

        # Create aligned table
        models_table = Table.grid(padding=(0, 2))
        models_table.add_column(style=f"{TEXT_PRIMARY}", justify="left")
        models_table.add_column(style=f"dim {TEXT_SECONDARY}", justify="right")

        for model_info in models_available.models:
            model_name = model_info.model
            size = model_info.details.parameter_size if hasattr(model_info, 'details') and hasattr(model_info.details, 'parameter_size') else ""
            models_table.add_row(f"  · {model_name}", size)

        console.print(Align.center(models_table))
        console.print()

    # Tools - horizontal layout (dynamic)
    if model.tool_executor and model.tool_executor.tools_definition:
        tools_text = Text()
        tools_text.append("TOOLS  ", style=f"bold {TEXT_SECONDARY}")

        tool_names = []
        for tool_def in model.tool_executor.tools_definition:
            if "function" in tool_def and "name" in tool_def["function"]:
                # Convert snake_case to readable format (e.g., "web_search" -> "search")
                name = tool_def["function"]["name"].replace("_", " ").split()[-1]
                tool_names.append(name)

        for idx, name in enumerate(tool_names):
            tools_text.append(name, style=f"{ACCENT_COLOR}")
            if idx < len(tool_names) - 1:
                tools_text.append(" · ", style=f"dim {TEXT_SECONDARY}")

        console.print(Align.center(tools_text))
        console.print()

    # Minimal help
    help_text = Text()
    help_text.append("Commands: ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/exit", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/clear", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/history", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/save [name]", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/load <name>", style=f"{TEXT_SECONDARY}")

    console.print(Align.center(help_text))
    console.print(f"{'─' * console.width}", style=f"dim {TEXT_SECONDARY}")
    console.print()

def show_thinking(full_content: str, live: Live, start_time: float):
    """Display thinking indicator while processing"""
    import random

    elapsed = time.time() - start_time

    # Extensive list of thinking/processing words
    thinking_words = [
        # Cognitive processes
        "pondering", "reasoning", "analyzing", "processing",
        "contemplating", "considering", "evaluating", "reflecting",
        "computing", "synthesizing", "deliberating", "examining",
        "inferring", "deducing", "interpreting", "assessing",
        "theorizing", "hypothesizing", "conceptualizing", "formulating",

        # Mental activities
        "cogitating", "ruminating", "meditating", "musing",
        "speculating", "surmising", "calculating", "reckoning",
        "discerning", "perceiving", "comprehending", "understanding",
        "grasping", "apprehending", "fathoming", "deciphering",

        # Analytical processes
        "dissecting", "parsing", "scrutinizing", "investigating",
        "exploring", "probing", "studying", "researching",
        "surveying", "reviewing", "inspecting", "auditing",
        "diagnosing", "troubleshooting", "debugging", "profiling",

        # Creative processes
        "ideating", "brainstorming", "innovating", "devising",
        "crafting", "designing", "architecting", "constructing",
        "composing", "authoring", "drafting", "sketching",
        "prototyping", "modeling", "simulating", "envisioning",

        # Decision-making
        "weighing", "judging", "determining", "resolving",
        "deciding", "choosing", "selecting", "prioritizing",
        "optimizing", "refining", "tuning", "calibrating",
        "balancing", "harmonizing", "reconciling", "integrating",

        # Data processing
        "aggregating", "collating", "indexing", "cataloging",
        "organizing", "structuring", "formatting", "transforming",
        "mapping", "filtering", "sorting", "ranking",
        "clustering", "classifying", "categorizing", "tagging",

        # Learning & adaptation
        "learning", "adapting", "evolving", "developing",
        "growing", "improving", "enhancing", "advancing",
        "progressing", "maturing", "refining", "perfecting"
    ]

    # Pick a random word based on elapsed time to have some variation
    word_index: int = int(start_time) % len(thinking_words)
    thinking_word = thinking_words[word_index].capitalize()

    # Minimal thinking indicator
    dots = "." * (int(elapsed * 2) % 4)
    thinking_text = Text()
    thinking_text.append("  ", style="")
    thinking_text.append("●", style=f"{BRAND_COLOR}")
    thinking_text.append(f" {thinking_word}", style=f"dim {TEXT_SECONDARY}")
    thinking_text.append(dots.ljust(3), style=f"dim {TEXT_SECONDARY}")
    thinking_text.append(f" {elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    if len(full_content) > 0:
        thinking_text.append(f" · {len(full_content)} chars", style=f"dim {TEXT_SECONDARY}")

    live.update(thinking_text)

def show_response(console: Console, elapsed: float, content: str):
    """Display the final response with markdown formatting"""
    # Clean header
    header = Text()
    header.append("  ● ", style=f"{SUCCESS_COLOR}")
    header.append(f"{elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    console.print(header)
    console.print()

    # Markdown content with minimal styling
    console.print(Markdown(content, code_theme="monokai"))
    console.print()
    console.print(f"{'─' * console.width}", style=f"dim {TEXT_SECONDARY}")
    console.print()

def show_tool_usage(tool_name: str, tool_args: dict):
    """Display tool usage information"""
    import json
    console = Console()

    # Minimal tool notification
    tool_text = Text()
    tool_text.append("  ▸ ", style=f"{WARNING_COLOR}")
    tool_text.append(f"{tool_name}", style=f"bold {TEXT_PRIMARY}")

    # Show key arguments inline
    if tool_args:
        key_arg = list(tool_args.values())[0] if tool_args else ""
        if isinstance(key_arg, str) and len(key_arg) < 50:
            tool_text.append(f"  {key_arg}", style=f"dim {TEXT_SECONDARY}")

    console.print(tool_text)

def show_tool_result(result: str):
    """Display tool execution result"""
    console = Console()
    # Just show a success indicator, result goes to model
    result_text = Text()
    result_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    result_text.append("completed", style=f"dim {TEXT_SECONDARY}")

    console.print(result_text)
    console.print()

def show_history(conversation_history: list):
    """Display conversation history"""
    console = Console()
    console.print()

    for idx, msg in enumerate(conversation_history, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        if role == "system":
            continue  # Skip system messages

        # Clean display
        if role == "user":
            prefix = Text()
            prefix.append("  → ", style=f"dim {TEXT_SECONDARY}")
            prefix.append("you", style=f"bold {TEXT_PRIMARY}")
            console.print(prefix)

            # Render markdown for user messages
            if content:
                console.print(Markdown(str(content)))

        elif role == "assistant":
            prefix = Text()
            prefix.append("  ● ", style=f"{BRAND_COLOR}")
            prefix.append("assistant", style=f"bold {TEXT_PRIMARY}")
            console.print(prefix)

            # Render markdown for assistant messages
            if content:
                console.print(Markdown(str(content)))

            # Show tool calls if present
            if tool_calls:
                for tool_call in tool_calls:
                    import json
                    tool_info = Text()
                    tool_info.append("    ▸ ", style=f"{WARNING_COLOR}")

                    # Handle both object and dict format
                    if hasattr(tool_call, 'function'):
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                    else:
                        tool_name = tool_call.get("function", {}).get("name", "unknown")
                        tool_args = tool_call.get("function", {}).get("arguments", {})

                    tool_info.append(f"{tool_name}", style=f"bold {TEXT_PRIMARY}")
                    tool_info.append(f" {json.dumps(tool_args, ensure_ascii=False)}", style=f"dim {TEXT_SECONDARY}")
                    console.print(tool_info)

        elif role == "tool":
            prefix = Text()
            prefix.append("  ▸ ", style=f"{WARNING_COLOR}")
            prefix.append("tool result", style=f"dim {TEXT_SECONDARY}")
            console.print(prefix)

            # Truncate long tool results
            if content:
                truncated = str(content)[:200]
                if len(str(content)) > 200:
                    truncated += "..."
                console.print(f"    {truncated}", style=f"dim {TEXT_SECONDARY}")

        console.print()

    console.print(f"{'─' * console.width}", style=f"dim {TEXT_SECONDARY}")
    console.print()

def show_error(error_msg: str):
    """Display error message"""
    console = Console()
    error_text = Text()
    error_text.append("  ✗ ", style="bold red")
    error_text.append("Error: ", style="bold red")
    error_text.append(error_msg, style=f"{TEXT_PRIMARY}")

    console.print()
    console.print(error_text)
    console.print()

def show_clear_confirmation():
    """Display confirmation that history was cleared"""
    console = Console()
    clear_text = Text()
    clear_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    clear_text.append("History cleared", style=f"{TEXT_SECONDARY}")

    console.print()
    console.print(clear_text)
    console.print()

def show_save_confirmation(filename: str):
    """Display confirmation that conversation was saved"""
    console = Console()
    save_text = Text()
    save_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    save_text.append("Conversation saved to ", style=f"{TEXT_SECONDARY}")
    save_text.append(filename, style=f"bold {TEXT_PRIMARY}")

    console.print()
    console.print(save_text)
    console.print()

def show_load_confirmation(filename: str, message_count: int):
    """Display confirmation that conversation was loaded"""
    console = Console()
    load_text = Text()
    load_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    load_text.append("Conversation loaded from ", style=f"{TEXT_SECONDARY}")
    load_text.append(filename, style=f"bold {TEXT_PRIMARY}")
    load_text.append(f" ({message_count} messages)", style=f"dim {TEXT_SECONDARY}")

    console.print()
    console.print(load_text)
    console.print()

def show_goodbye():
    """Display goodbye message"""
    console = Console()
    console.print()
    goodbye = Text("Goodbye", style=f"dim {TEXT_SECONDARY}")
    console.print(Align.center(goodbye))
    console.print()

def show_image_found(image_paths: list, prompt: str):
    """Display information about found images"""
    console = Console()

    image_text = Text()
    image_text.append("  ▸ ", style=f"{WARNING_COLOR}")
    image_text.append(f"vision: {len(image_paths)} image(s) attached", style=f"dim {TEXT_SECONDARY}")

    console.print(image_text)
    console.print()
