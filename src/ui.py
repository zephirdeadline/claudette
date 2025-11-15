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
import tiktoken

if TYPE_CHECKING:
    from .models import Model

# Professional color scheme
BRAND_COLOR = "#7C3AED"  # Purple
ACCENT_COLOR = "#10B981"  # Green
TEXT_PRIMARY = "#E5E7EB"  # Light gray
TEXT_SECONDARY = "#9CA3AF"  # Medium gray
SUCCESS_COLOR = "#10B981"  # Green
WARNING_COLOR = "#F59E0B"  # Amber

# Initialize tokenizer (using cl100k_base encoding which is used by GPT-4 and similar models)
_tokenizer = None

def get_token_count(text: str) -> int:
    """Count the number of tokens in a text string"""
    global _tokenizer
    if _tokenizer is None:
        try:
            _tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to a simple character-based estimation if tiktoken fails
            return len(text) // 4  # Rough estimate: ~4 chars per token

    try:
        return len(_tokenizer.encode(text))
    except Exception:
        return len(text) // 4


def serialize_message_for_tokens(message: dict) -> str:
    """Serialize a message to a string representation for token counting"""
    import json

    def default_serializer(obj):
        """Custom serializer for non-JSON-serializable objects"""
        if hasattr(obj, 'function'):
            return {
                "function": {
                    "name": obj.function.name,
                    "arguments": obj.function.arguments
                }
            }
        return str(obj)

    try:
        return json.dumps(message, default=default_serializer)
    except Exception:
        return str(message)


def get_conversation_token_count(conversation_history: list) -> int:
    """Count the total number of tokens in the conversation history"""
    total_tokens = 0

    for message in conversation_history:
        # Serialize entire message and count tokens
        message_str = serialize_message_for_tokens(message)
        total_tokens += get_token_count(message_str)

    return total_tokens


def show_welcome(model: "Model", host: str, ollama_models_available: list):
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
    from .models import ModelFactory

    # Get all models from Ollama and from config
    ollama_model_names = set()
    if len(ollama_models_available.models) > 0:
        ollama_model_names = {model_info.model for model_info in ollama_models_available.models}

    configured_models = set(ModelFactory.get_available_models())

    # Combine both sets to show all models
    all_models = ollama_model_names | configured_models

    if len(all_models) > 0:
        models_header = Text()
        models_header.append(f"MODELS ({len(all_models)})", style=f"bold {TEXT_SECONDARY}")
        console.print(Align.center(models_header))
        console.print()

        # Create aligned table with status indicator
        models_table = Table.grid(padding=(0, 2))
        models_table.add_column(style=f"{TEXT_PRIMARY}", justify="left")  # Model name
        models_table.add_column(style=f"dim {TEXT_SECONDARY}", justify="right")  # Size
        models_table.add_column(style=f"{TEXT_PRIMARY}", justify="center")  # Status

        # Sort models alphabetically
        for model_name in sorted(all_models):
            # Get size from Ollama if available
            size = ""
            for model_info in ollama_models_available.models:
                if model_info.model == model_name:
                    size = model_info.details.parameter_size if hasattr(model_info, 'details') and hasattr(model_info.details, 'parameter_size') else ""
                    break

            # Determine status
            in_ollama = model_name in ollama_model_names
            in_config = model_name in configured_models

            if in_ollama and in_config:
                # Ready to use
                status_indicator = "✓"
                status_color = SUCCESS_COLOR
            elif in_ollama and not in_config:
                # In Ollama but not configured
                status_indicator = "⚠"
                status_color = WARNING_COLOR
            elif not in_ollama and in_config:
                # Configured but not in Ollama
                status_indicator = "✗"
                status_color = "red"
            else:
                # Should not happen
                status_indicator = "?"
                status_color = TEXT_SECONDARY

            # Create status text with color
            status_text = Text(status_indicator, style=status_color)

            models_table.add_row(f"  · {model_name}", size, status_text)

        console.print(Align.center(models_table))

        # Legend for status indicators
        legend = Text()
        legend.append("  ", style="")
        legend.append("✓", style=SUCCESS_COLOR)
        legend.append(" Ready  ", style=f"dim {TEXT_SECONDARY}")
        legend.append("⚠", style=WARNING_COLOR)
        legend.append(" Missing config  ", style=f"dim {TEXT_SECONDARY}")
        legend.append("✗", style="red")
        legend.append(" Not in Ollama", style=f"dim {TEXT_SECONDARY}")
        console.print(Align.center(legend))
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
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/model <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/unload", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/pull <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/info <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/temperature <value>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/validate", style=f"{TEXT_SECONDARY}")

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
        token_count = get_token_count(full_content)
        thinking_text.append(f" · {token_count} tokens", style=f"dim {TEXT_SECONDARY}")

    live.update(thinking_text)

def show_response(console: Console, elapsed: float, content: str):
    """Display the final response with markdown formatting"""
    # Clean header
    header = Text()
    header.append("  ● ", style=f"{SUCCESS_COLOR}")
    header.append(f"{elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    # Add token count
    token_count = get_token_count(content)
    header.append(f" · {token_count} tokens", style=f"dim {TEXT_SECONDARY}")

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

def show_model_unload_start():
    """Display model unloading start message"""
    console = Console()
    console.print(Text("  ⏳ Unloading current model...", style=f"dim {TEXT_SECONDARY}"))

def show_model_switch_success(model_name: str):
    """Display model switch success message"""
    console = Console()
    success_text = Text()
    success_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    success_text.append(f"Switched to model: {model_name}", style=f"{TEXT_SECONDARY}")
    console.print()
    console.print(success_text)
    console.print()

def show_model_unload_success():
    """Display model unload success message"""
    console = Console()
    unload_text = Text()
    unload_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    unload_text.append("Model unloaded from memory", style=f"{TEXT_SECONDARY}")
    console.print()
    console.print(unload_text)
    console.print()

def show_pull_start(model_name: str):
    """Display pull start message"""
    console = Console()
    pull_text = Text()
    pull_text.append("  ⏳ ", style=f"{WARNING_COLOR}")
    pull_text.append(f"Pulling model: {model_name}", style=f"{TEXT_SECONDARY}")
    console.print()
    console.print(pull_text)
    console.print()

def show_pull_success(model_name: str):
    """Display pull success message"""
    console = Console()
    success_text = Text()
    success_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
    success_text.append(f"Successfully pulled model: {model_name}", style=f"{TEXT_SECONDARY}")
    console.print()
    console.print(success_text)
    console.print()

def show_model_info(model_name: str, model_info: dict):
    """Display model information in a formatted panel"""
    console = Console()

    try:
        console.print()

        # Create info panel
        from rich.panel import Panel
        from rich.table import Table

        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style=f"bold {TEXT_SECONDARY}", justify="right", width=20)
        info_table.add_column(style=f"{TEXT_PRIMARY}")

        # Basic info
        info_table.add_row("Model", model_name)

        # Details section
        details = model_info.get('details', {})
        if details:
            if hasattr(details, 'format'):
                info_table.add_row("Format", details.format.upper())
            if hasattr(details, 'family'):
                info_table.add_row("Family", details.family)
            if hasattr(details, 'parameter_size'):
                info_table.add_row("Size", details.parameter_size)
            if hasattr(details, 'quantization_level'):
                info_table.add_row("Quantization", details.quantization_level)

        # Model info section - extract context length
        modelinfo = model_info.get('modelinfo', {})
        if modelinfo:
            # Try to get context length from different possible keys
            context_length = None
            for key in modelinfo.keys():
                if 'context_length' in key:
                    context_length = modelinfo[key]
                    break

            if context_length:
                # Format large numbers with K/M suffix
                if context_length >= 1000000:
                    context_str = f"{context_length / 1000000:.1f}M tokens"
                elif context_length >= 1000:
                    context_str = f"{context_length / 1000:.0f}K tokens"
                else:
                    context_str = f"{context_length} tokens"
                info_table.add_row("Context Window", context_str)

        # Capabilities section
        capabilities = model_info.get('capabilities', [])
        if capabilities:
            # Check for vision support
            has_vision = 'vision' in capabilities
            info_table.add_row("Vision Support", "✓ Yes" if has_vision else "✗ No")

            # Check for tools/function calling support
            has_tools = 'tools' in capabilities or 'function_calling' in capabilities
            info_table.add_row("Tools Support", "✓ Yes" if has_tools else "✗ No")

            # List all capabilities
            caps_str = ", ".join(capabilities)
            info_table.add_row("Capabilities", caps_str)

        # Modified date
        if hasattr(model_info, 'modified_at'):
            modified_str = model_info.modified_at.strftime("%Y-%m-%d %H:%M")
            info_table.add_row("Modified", modified_str)

        # Parameters section - show key parameters
        parameters = model_info.get('parameters', '')
        if parameters:
            import re
            # Extract temperature
            temp_match = re.search(r'temperature\s+([\d.]+)', parameters)
            if temp_match:
                info_table.add_row("Temperature", temp_match.group(1))

            # Extract top_k
            top_k_match = re.search(r'top_k\s+([\d]+)', parameters)
            if top_k_match:
                info_table.add_row("Top K", top_k_match.group(1))

            # Extract top_p
            top_p_match = re.search(r'top_p\s+([\d.]+)', parameters)
            if top_p_match:
                info_table.add_row("Top P", top_p_match.group(1))

        # Check if configured in Claudette
        from .models import ModelFactory
        is_configured = ModelFactory.is_model_ready(model_name)
        config_status = f"{'✓ Ready' if is_configured else '⚠ Not configured'}"
        status_style = SUCCESS_COLOR if is_configured else WARNING_COLOR
        status_text = Text(config_status, style=status_style)
        info_table.add_row("Claudette Status", status_text)

        console.print(Panel(
            info_table,
            title=f"[bold {BRAND_COLOR}]Model Information[/bold {BRAND_COLOR}]",
            border_style=f"dim {TEXT_SECONDARY}",
            padding=(1, 2)
        ))
        console.print()

    except Exception as e:
        show_error(f"Failed to format model info: {e}")


def show_temperature_change(temperature: float):
    """Display temperature change confirmation"""
    console = Console()
    console.print()
    console.print(
        f"  [dim {TEXT_SECONDARY}]→[/dim {TEXT_SECONDARY}] Temperature set to [bold {ACCENT_COLOR}]{temperature}[/bold {ACCENT_COLOR}]"
    )
    console.print()


def show_validation_change(validation_enabled: bool):
    """Display validation status change confirmation"""
    console = Console()
    validation_text = Text()
    validation_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")

    if validation_enabled:
        validation_text.append("Tool validation ", style=f"{TEXT_SECONDARY}")
        validation_text.append("enabled", style=f"bold {SUCCESS_COLOR}")
        validation_text.append(" 🛡️", style=f"{SUCCESS_COLOR}")
    else:
        validation_text.append("Tool validation ", style=f"{TEXT_SECONDARY}")
        validation_text.append("disabled", style=f"bold {WARNING_COLOR}")
        validation_text.append(" ⚠️", style=f"{WARNING_COLOR}")

    console.print()
    console.print(validation_text)
    console.print()
