"""
UI and display utilities for Claudette
"""

import time
import json
import re
import math
import random
from typing import TYPE_CHECKING
from datetime import datetime
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
    from .models import Model, ModelFactory
else:
    # Import for runtime use
    from .models import ModelFactory

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

    def default_serializer(obj):
        """Custom serializer for non-JSON-serializable objects"""
        if hasattr(obj, "function"):
            return {
                "function": {
                    "name": obj.function.name,
                    "arguments": obj.function.arguments,
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

    # Mascot and header - minimalist block design
    console.print()

    # Create the full banner as a single block
    banner = Table.grid(padding=0)
    banner.add_column(justify="left")

    # Build the banner lines - Sleek cat/feline mascot
    line1 = Text()
    line1.append(" ╱╲   ╱╲   ", style=f"{BRAND_COLOR}")
    line1.append("claudette ", style=f"bold {BRAND_COLOR}")
    line1.append("v1.0", style=f"dim {TEXT_SECONDARY}")

    line2 = Text()
    line2.append("│ ◉ ▼ ◉ │  ", style=f"{BRAND_COLOR}")
    line2.append(f"{model.name}", style=f"{TEXT_PRIMARY}")
    line2.append(" · ", style=f"dim {TEXT_SECONDARY}")
    line2.append("Local LLM", style=f"dim {TEXT_SECONDARY}")

    line3 = Text()
    line3.append(" ╲  ω  ╱   ", style=f"{BRAND_COLOR}")

    line4 = Text()
    line4.append("  ▔▔▔▔▔    ", style=f"dim {BRAND_COLOR}")

    banner.add_row(line1)
    banner.add_row(line2)
    banner.add_row(line3)
    banner.add_row(line4)

    console.print(Align.center(banner))
    console.print()

    # Clean info grid
    info_grid = Table.grid(padding=(0, 2))
    info_grid.add_column(style=f"{TEXT_SECONDARY}", justify="right", width=15)
    info_grid.add_column(style=f"bold {TEXT_PRIMARY}")

    # Vision status with color coding
    vision_status = Text()
    if model.image_mode:
        vision_status.append("enabled", style=f"bold {SUCCESS_COLOR}")
    else:
        vision_status.append("disabled", style=f"bold red")

    info_grid.add_row("MODEL", model.name)
    info_grid.add_row("HOST", host)
    info_grid.add_row("VISION", vision_status)

    console.print(
        Panel(
            Align.center(info_grid),
            box=box.ROUNDED,
            border_style=f"dim {TEXT_SECONDARY}",
            padding=(1, 4),
        )
    )

    # Available models - complete list with aligned table
    # Get all models from Ollama and from config
    ollama_model_names = set()
    if len(ollama_models_available.models) > 0:
        ollama_model_names = {
            model_info.model for model_info in ollama_models_available.models
        }

    configured_models = set(ModelFactory.get_available_models())

    # Combine both sets to show all models
    all_models = ollama_model_names | configured_models

    if len(all_models) > 0:
        models_header = Text()
        models_header.append(
            f"MODELS ({len(all_models)})", style=f"bold {TEXT_SECONDARY}"
        )
        console.print(Align.center(models_header))
        console.print()

        # Create aligned table with status indicator and capabilities
        models_table = Table(
            show_header=False, show_edge=False, pad_edge=False, box=None, padding=(0, 2)
        )
        models_table.add_column(
            style=f"{TEXT_PRIMARY}", justify="left", no_wrap=True
        )  # Model name
        models_table.add_column(
            style=f"dim {TEXT_SECONDARY}", justify="right", width=6, no_wrap=True
        )  # Size
        models_table.add_column(
            style=f"{TEXT_PRIMARY}", justify="left", width=2, no_wrap=True
        )  # Vision
        models_table.add_column(
            style=f"{TEXT_PRIMARY}", justify="left", width=2, no_wrap=True
        )  # Tools
        models_table.add_column(
            style=f"{TEXT_PRIMARY}", justify="left", width=2, no_wrap=True
        )  # Thinking
        models_table.add_column(
            style=f"{TEXT_PRIMARY}", justify="center", width=2, no_wrap=True
        )  # Status

        # Sort models alphabetically
        for model_name in sorted(all_models):
            # Get size and capabilities from Ollama if available
            size = ""
            vision_icon = ""
            tools_icon = ""
            thinking_icon = ""

            in_ollama = model_name in ollama_model_names

            if in_ollama:
                for model_info in ollama_models_available.models:
                    if model_info.model == model_name:
                        size = (
                            model_info.details.parameter_size
                            if hasattr(model_info, "details")
                            and hasattr(model_info.details, "parameter_size")
                            else ""
                        )

                        # Get capabilities from Ollama
                        try:
                            model_data = model.ollama_client.show(model_name)
                            capabilities = model_data.get("capabilities", [])

                            # Check for vision
                            vision_icon = "👀" if "vision" in capabilities else " ·"

                            # Check for tools
                            tools_icon = (
                                "🔧"
                                if (
                                    "tools" in capabilities
                                    or "function_calling" in capabilities
                                )
                                else "·"
                            )

                            # Check for thinking (reasoning)
                            thinking_icon = (
                                "🧠"
                                if (
                                    "reasoning" in capabilities
                                    or "thinking" in capabilities
                                )
                                else "·"
                            )

                        except Exception:
                            vision_icon = " ·"
                            tools_icon = " ·"
                            thinking_icon = " ·"

                        break
            else:
                # Model not in Ollama
                vision_icon = "?"
                tools_icon = "?"
                thinking_icon = "?"

            # Determine status
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

            # Create individual Text objects for each cell
            vision_text = Text(
                vision_icon,
                style=SUCCESS_COLOR if vision_icon == "👁️" else "dim #6B7280",
            )
            tools_text = Text(
                tools_icon, style=SUCCESS_COLOR if tools_icon == "🔧" else "dim #6B7280"
            )
            thinking_text = Text(
                thinking_icon,
                style=SUCCESS_COLOR if thinking_icon == "🧠" else "dim #6B7280",
            )
            status_text = Text(status_indicator, style=status_color)

            models_table.add_row(
                f"  · {model_name}",
                size,
                vision_text,
                tools_text,
                thinking_text,
                status_text,
            )

        console.print(Align.center(models_table))

        # Legend for status indicators and capabilities
        legend_status = Text()
        legend_status.append("  ", style="")
        legend_status.append("✓", style=SUCCESS_COLOR)
        legend_status.append(" Ready  ", style=f"dim {TEXT_SECONDARY}")
        legend_status.append("⚠ ", style=WARNING_COLOR)
        legend_status.append(" Missing config  ", style=f"dim {TEXT_SECONDARY}")
        legend_status.append("✗", style="red")
        legend_status.append(" Not in Ollama", style=f"dim {TEXT_SECONDARY}")
        console.print(Align.center(legend_status))

        # Legend for capabilities
        legend_caps = Text()
        legend_caps.append("  ", style="")
        legend_caps.append("👁️", style=SUCCESS_COLOR)
        legend_caps.append(" Vision  ", style=f"dim {TEXT_SECONDARY}")
        legend_caps.append("🔧", style=SUCCESS_COLOR)
        legend_caps.append(" Tools  ", style=f"dim {TEXT_SECONDARY}")
        legend_caps.append("🧠", style=SUCCESS_COLOR)
        legend_caps.append(" Thinking", style=f"dim {TEXT_SECONDARY}")
        console.print(Align.center(legend_caps))
        console.print()

    # Tools - horizontal layout (dynamic)
    if model.tool_executor and model.tool_executor.tools_definition:
        tools_text = Text()
        tools_text.append("TOOLS  ", style=f"bold {TEXT_SECONDARY}")

        # Map tool names to display names
        tool_display_names = {
            "ask_user": "ask",
            "web_search": "search",
            "read_file": "read",
            "write_file": "write",
            "edit_file": "edit",
            "execute_command": "shell",
            "get_current_time": "time",
            "list_directory": "ls",
        }

        tool_names = []
        for tool_def in model.tool_executor.tools_definition:
            if "function" in tool_def and "name" in tool_def["function"]:
                tool_name = tool_def["function"]["name"]
                display_name = tool_display_names.get(tool_name, tool_name)
                tool_names.append(display_name)

        for idx, name in enumerate(tool_names):
            tools_text.append(name, style=f"{ACCENT_COLOR}")
            if idx < len(tool_names) - 1:
                tools_text.append(" · ", style=f"dim {TEXT_SECONDARY}")

        console.print(Align.center(tools_text))
        console.print()

    # Minimal help - Commands in alphabetical order
    help_text = Text()
    help_text.append("Commands: ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/clear", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/conversations", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/exit", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/history", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/info <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/init", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/load <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/model <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/models", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/prompt", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/pull <name>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/reprompting", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/save [name]", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/stats", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/temperature <value>", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/thinking", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/unload", style=f"{TEXT_SECONDARY}")
    help_text.append(" · ", style=f"dim {TEXT_SECONDARY}")
    help_text.append("/validate", style=f"{TEXT_SECONDARY}")

    console.print(Align.center(help_text))
    console.print(f"{'─' * console.width}", style=f"dim {TEXT_SECONDARY}")
    console.print()


def show_thinking(
    full_content: str, live: Live, start_time: float, thinking_content: str = ""
):
    """Display thinking indicator while processing"""
    elapsed = time.time() - start_time

    # Extensive list of thinking/processing words
    thinking_words = [
        # Cognitive processes
        "pondering",
        "reasoning",
        "analyzing",
        "processing",
        "contemplating",
        "considering",
        "evaluating",
        "reflecting",
        "computing",
        "synthesizing",
        "deliberating",
        "examining",
        "inferring",
        "deducing",
        "interpreting",
        "assessing",
        "theorizing",
        "hypothesizing",
        "conceptualizing",
        "formulating",
        # Mental activities
        "cogitating",
        "ruminating",
        "meditating",
        "musing",
        "speculating",
        "surmising",
        "calculating",
        "reckoning",
        "discerning",
        "perceiving",
        "comprehending",
        "understanding",
        "grasping",
        "apprehending",
        "fathoming",
        "deciphering",
        # Analytical processes
        "dissecting",
        "parsing",
        "scrutinizing",
        "investigating",
        "exploring",
        "probing",
        "studying",
        "researching",
        "surveying",
        "reviewing",
        "inspecting",
        "auditing",
        "diagnosing",
        "troubleshooting",
        "debugging",
        "profiling",
        # Creative processes
        "ideating",
        "brainstorming",
        "innovating",
        "devising",
        "crafting",
        "designing",
        "architecting",
        "constructing",
        "composing",
        "authoring",
        "drafting",
        "sketching",
        "prototyping",
        "modeling",
        "simulating",
        "envisioning",
        # Decision-making
        "weighing",
        "judging",
        "determining",
        "resolving",
        "deciding",
        "choosing",
        "selecting",
        "prioritizing",
        "optimizing",
        "refining",
        "tuning",
        "calibrating",
        "balancing",
        "harmonizing",
        "reconciling",
        "integrating",
        # Data processing
        "aggregating",
        "collating",
        "indexing",
        "cataloging",
        "organizing",
        "structuring",
        "formatting",
        "transforming",
        "mapping",
        "filtering",
        "sorting",
        "ranking",
        "clustering",
        "classifying",
        "categorizing",
        "tagging",
        # Learning & adaptation
        "learning",
        "adapting",
        "evolving",
        "developing",
        "growing",
        "improving",
        "enhancing",
        "advancing",
        "progressing",
        "maturing",
        "refining",
        "perfecting",
    ]

    # Pick a random word based on elapsed time to have some variation
    word_index: int = int(start_time) % len(thinking_words)
    thinking_word = thinking_words[word_index].capitalize()

    # Animated thinking indicator with pulsing dot
    dots = "." * (int(elapsed * 2) % 4)

    # Calculate pulsing effect for the dot
    # Pulse speed: ~2 pulses per second
    pulse_phase = (elapsed * 2) % 1.0  # 0.0 to 1.0
    # Create smooth sine wave for size: 0.5 -> 1.0 -> 0.5
    pulse_intensity = 0.5 + 0.5 * abs(math.sin(pulse_phase * math.pi))

    # Choose dot character based on pulse phase
    # Cycle through different sizes for visual pulse effect
    pulse_cycle = int((elapsed * 4) % 3)
    if pulse_cycle == 0:
        dot_char = "●"  # Large
    elif pulse_cycle == 1:
        dot_char = "◉"  # Medium with ring
    else:
        dot_char = "○"  # Small/hollow

    thinking_text = Text()
    thinking_text.append("  ", style="")
    thinking_text.append(dot_char, style=f"{BRAND_COLOR}")
    thinking_text.append(f" {thinking_word}", style=f"dim {TEXT_SECONDARY}")
    thinking_text.append(dots.ljust(3), style=f"dim {TEXT_SECONDARY}")
    thinking_text.append(f" {elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    if len(full_content) > 0:
        token_count = get_token_count(full_content)
        thinking_text.append(f" · {token_count} tokens", style=f"dim {TEXT_SECONDARY}")

    # Display thinking content if present
    if thinking_content:
        thinking_token_count = get_token_count(thinking_content)
        thinking_text.append(
            f" · 🧠 {thinking_token_count} thinking tokens",
            style=f"bold {WARNING_COLOR}",
        )

        # Create a group with header and thinking content preview
        thinking_preview = (
            thinking_content[-200:] if len(thinking_content) > 200 else thinking_content
        )
        thinking_display = Group(
            thinking_text,
            Text(""),
            Panel(
                Text(thinking_preview, style=f"italic {TEXT_SECONDARY}"),
                title="[bold]💭 Thinking[/bold]",
                border_style=f"{WARNING_COLOR}",
                box=box.ROUNDED,
                padding=(0, 1),
            ),
        )
        live.update(thinking_display)
    else:
        live.update(thinking_text)


def render_math_content(content: str) -> str:
    """
    Enhance mathematical expressions for terminal display.
    Converts LaTeX math expressions to a more readable format.
    """
    # Pattern for inline math $...$
    inline_pattern = r"\$([^\$]+)\$"
    # Pattern for display math $$...$$
    display_pattern = r"\$\$([^\$]+)\$\$"

    # Replace display math with highlighted blocks
    def replace_display_math(match):
        expr = match.group(1).strip()
        # Add visual separation for display math
        return f"\n\n**[Math Expression]**\n```\n{expr}\n```\n"

    # Replace inline math with highlighted text
    def replace_inline_math(match):
        expr = match.group(1).strip()
        # Keep inline math visible with backticks
        return f"`{expr}`"

    # Process display math first ($$...$$)
    content = re.sub(display_pattern, replace_display_math, content)

    # Then process inline math ($...$)
    content = re.sub(inline_pattern, replace_inline_math, content)

    return content


def show_response(
    console: Console, elapsed: float, content: str, thinking_content: str = ""
):
    """Display the final response with markdown formatting"""
    # Clean header
    header = Text()
    header.append("  ● ", style=f"{SUCCESS_COLOR}")
    header.append(f"{elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    # Add token count
    token_count = get_token_count(content)
    header.append(f" · {token_count} tokens", style=f"dim {TEXT_SECONDARY}")

    # Show thinking token count if present
    if thinking_content:
        thinking_token_count = get_token_count(thinking_content)
        header.append(
            f" · 🧠 {thinking_token_count} thinking tokens",
            style=f"bold {WARNING_COLOR}",
        )

    console.print(header)
    console.print()

    # Display thinking content in a collapsible panel if present
    if thinking_content:
        # Enhance math rendering for thinking content
        enhanced_thinking = render_math_content(thinking_content)
        console.print(
            Panel(
                Markdown(enhanced_thinking, code_theme="monokai"),
                title="[bold]💭 Thinking Process[/bold]",
                border_style=f"{WARNING_COLOR}",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()

    # Enhance math rendering for main content
    enhanced_content = render_math_content(content)

    # Markdown content with minimal styling
    console.print(Markdown(enhanced_content, code_theme="monokai"))
    console.print()
    console.print(f"{'─' * console.width}", style=f"dim {TEXT_SECONDARY}")
    console.print()


def show_tool_usage(tool_name: str, tool_args: dict):
    """Display tool usage information"""
    console = Console()

    # Tool header
    tool_text = Text()
    tool_text.append("  ▸ ", style=f"{WARNING_COLOR}")
    tool_text.append(f"{tool_name}", style=f"bold {TEXT_PRIMARY}")
    console.print(tool_text)

    # Show all arguments with details
    if tool_args:
        for arg_name, arg_value in tool_args.items():
            arg_text = Text()
            arg_text.append("    ", style="")
            arg_text.append(f"{arg_name}: ", style=f"bold {WARNING_COLOR}")

            # Format the argument value based on its type
            if isinstance(arg_value, str):
                # Truncate long strings for readability
                if len(arg_value) > 100:
                    display_value = arg_value[:100] + "..."
                else:
                    display_value = arg_value
                # Replace newlines with visible indicator
                display_value = display_value.replace(
                    "\n", "↵\n    " + " " * (len(arg_name) + 2)
                )
                arg_text.append(f'"{display_value}"', style=f"{WARNING_COLOR}")
            elif isinstance(arg_value, (int, float, bool)):
                arg_text.append(str(arg_value), style=f"{WARNING_COLOR}")
            elif isinstance(arg_value, (list, dict)):
                # Pretty print JSON for complex types
                json_str = json.dumps(arg_value, indent=2, ensure_ascii=False)
                if len(json_str) > 100:
                    json_str = json_str[:100] + "..."
                arg_text.append(json_str, style=f"{WARNING_COLOR}")
            else:
                arg_text.append(str(arg_value), style=f"{WARNING_COLOR}")

            console.print(arg_text)

    console.print()


def show_tool_result(result: str):
    """Display tool execution result with partial output preview"""
    console = Console()

    # Check if result contains an error
    is_error = result.startswith("Error:") or "error" in result.lower()[:100]

    # Show success or error indicator
    result_text = Text()
    if is_error:
        result_text.append("  ✗ ", style=f"bold #EF4444")  # Red cross
        result_text.append("error", style=f"bold #EF4444")
    else:
        result_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")
        result_text.append("completed", style=f"dim {TEXT_SECONDARY}")
    console.print(result_text)

    # Display partial output preview
    if result:
        MAX_PREVIEW_LENGTH = 500  # Maximum characters to show
        MAX_LINES = 10  # Maximum lines to show

        # Show partial output header
        output_header = Text()
        if is_error:
            output_header.append("    ❌ Error output: ", style=f"bold #EF4444")
        else:
            output_header.append(
                "    📄 Output preview: ", style=f"bold {ACCENT_COLOR}"
            )
        console.print(output_header)

        # Prepare output preview
        result_lines = result.split("\n")
        preview_lines = result_lines[:MAX_LINES]
        preview_text = "\n".join(preview_lines)

        # Truncate if too long
        if len(preview_text) > MAX_PREVIEW_LENGTH:
            preview_text = preview_text[:MAX_PREVIEW_LENGTH] + "..."

        # Display preview in a subtle panel
        preview_panel = Panel(
            preview_text,
            border_style=f"bold #EF4444" if is_error else f"dim {TEXT_SECONDARY}",
            padding=(0, 1),
            box=box.ROUNDED,
            style=f"#EF4444" if is_error else "",
        )
        console.print(preview_panel)

        # Show statistics
        total_lines = len(result_lines)
        total_chars = len(result)
        stats_text = Text()
        stats_text.append("    ", style="")
        stats_text.append("📊 ", style=f"{TEXT_SECONDARY}")
        stats_text.append(
            f"Total: {total_lines} line(s), {total_chars} character(s)",
            style=f"dim {TEXT_SECONDARY}",
        )

        if total_lines > MAX_LINES:
            stats_text.append(
                f" ({total_lines - MAX_LINES} more lines hidden)",
                style=f"italic dim {TEXT_SECONDARY}",
            )

        console.print(stats_text)

        # Extract and display URLs found in the result
        url_pattern = r'https?://[^\s\)\]"\'>]+'
        urls = re.findall(url_pattern, result)

        if urls:
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            # Display URLs
            urls_text = Text()
            urls_text.append("    ", style="")
            urls_text.append(
                f"🔗 {len(unique_urls)} URL(s): ", style=f"bold {WARNING_COLOR}"
            )
            console.print(urls_text)

            for url in unique_urls[:5]:  # Limit to 5 URLs to avoid clutter
                url_line = Text()
                url_line.append("      • ", style=f"dim {TEXT_SECONDARY}")
                url_line.append(url, style=f"{WARNING_COLOR}")
                console.print(url_line)

            if len(unique_urls) > 5:
                more_text = Text()
                more_text.append(
                    f"      ... and {len(unique_urls) - 5} more",
                    style=f"dim {TEXT_SECONDARY}",
                )
                console.print(more_text)

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
                    tool_info = Text()
                    tool_info.append("    ▸ ", style=f"{WARNING_COLOR}")

                    # Handle both object and dict format
                    if hasattr(tool_call, "function"):
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                    else:
                        tool_name = tool_call.get("function", {}).get("name", "unknown")
                        tool_args = tool_call.get("function", {}).get("arguments", {})

                    tool_info.append(f"{tool_name}", style=f"bold {TEXT_PRIMARY}")
                    tool_info.append(
                        f" {json.dumps(tool_args, ensure_ascii=False)}",
                        style=f"dim {TEXT_SECONDARY}",
                    )
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
    image_text.append(
        f"vision: {len(image_paths)} image(s) attached", style=f"dim {TEXT_SECONDARY}"
    )

    console.print(image_text)
    console.print()


def show_model_unload_start():
    """Display model unloading start message"""
    console = Console()
    console.print(
        Text("  ⏳ Unloading current model...", style=f"dim {TEXT_SECONDARY}")
    )


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
    success_text.append(
        f"Successfully pulled model: {model_name}", style=f"{TEXT_SECONDARY}"
    )
    console.print()
    console.print(success_text)
    console.print()


def show_model_info(model_name: str, model_info: dict):
    """Display model information in a formatted panel"""
    console = Console()

    try:
        console.print()

        # Create info panel
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style=f"bold {TEXT_SECONDARY}", justify="right", width=20)
        info_table.add_column(style=f"{TEXT_PRIMARY}")

        # Basic info
        info_table.add_row("Model", model_name)

        # Details section
        details = model_info.get("details", {})
        if details:
            if hasattr(details, "format"):
                info_table.add_row("Format", details.format.upper())
            if hasattr(details, "family"):
                info_table.add_row("Family", details.family)
            if hasattr(details, "parameter_size"):
                info_table.add_row("Size", details.parameter_size)
            if hasattr(details, "quantization_level"):
                info_table.add_row("Quantization", details.quantization_level)

        # Model info section - extract context length
        modelinfo = model_info.get("modelinfo", {})
        if modelinfo:
            # Try to get context length from different possible keys
            context_length = None
            for key in modelinfo.keys():
                if "context_length" in key:
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
        capabilities = model_info.get("capabilities", [])
        if capabilities:
            # Check for vision support
            has_vision = "vision" in capabilities
            info_table.add_row("Vision Support", "✓ Yes" if has_vision else "✗ No")

            # Check for tools/function calling support
            has_tools = "tools" in capabilities or "function_calling" in capabilities
            info_table.add_row("Tools Support", "✓ Yes" if has_tools else "✗ No")

            # List all capabilities
            caps_str = ", ".join(capabilities)
            info_table.add_row("Capabilities", caps_str)

        # Modified date
        if hasattr(model_info, "modified_at"):
            modified_str = model_info.modified_at.strftime("%Y-%m-%d %H:%M")
            info_table.add_row("Modified", modified_str)

        # Parameters section - show key parameters
        parameters = model_info.get("parameters", "")
        if parameters:
            # Extract temperature
            temp_match = re.search(r"temperature\s+([\d.]+)", parameters)
            if temp_match:
                info_table.add_row("Temperature", temp_match.group(1))

            # Extract top_k
            top_k_match = re.search(r"top_k\s+([\d]+)", parameters)
            if top_k_match:
                info_table.add_row("Top K", top_k_match.group(1))

            # Extract top_p
            top_p_match = re.search(r"top_p\s+([\d.]+)", parameters)
            if top_p_match:
                info_table.add_row("Top P", top_p_match.group(1))

        # Check if configured in Claudette
        is_configured = ModelFactory.is_model_ready(model_name)
        config_status = f"{'✓ Ready' if is_configured else '⚠ Not configured'}"
        status_style = SUCCESS_COLOR if is_configured else WARNING_COLOR
        status_text = Text(config_status, style=status_style)
        info_table.add_row("Claudette Status", status_text)

        console.print(
            Panel(
                info_table,
                title=f"[bold {BRAND_COLOR}]Model Information[/bold {BRAND_COLOR}]",
                border_style=f"dim {TEXT_SECONDARY}",
                padding=(1, 2),
            )
        )
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


def show_thinking_change(thinking_enabled: bool):
    """Display thinking mode status change confirmation"""
    console = Console()
    thinking_text = Text()
    thinking_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")

    if thinking_enabled:
        thinking_text.append("Thinking mode ", style=f"{TEXT_SECONDARY}")
        thinking_text.append("enabled", style=f"bold {SUCCESS_COLOR}")
        thinking_text.append(" 🧠", style=f"{SUCCESS_COLOR}")
    else:
        thinking_text.append("Thinking mode ", style=f"{TEXT_SECONDARY}")
        thinking_text.append("disabled", style=f"bold {TEXT_SECONDARY}")
        thinking_text.append(" 🧠", style=f"{TEXT_SECONDARY}")

    console.print()
    console.print(thinking_text)
    console.print()


def show_models_list(models_response: dict):
    """Display list of available models"""
    console = Console()

    console.print()

    # Create header
    header = Text()
    header.append("  Available Models", style=f"bold {BRAND_COLOR}")
    console.print(header)
    console.print()

    # Create table
    table = Table(
        show_header=True,
        header_style=f"bold {BRAND_COLOR}",
        border_style=f"dim {TEXT_SECONDARY}",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    table.add_column("Model Name", style=f"{TEXT_PRIMARY}", no_wrap=False)
    table.add_column("Size", style=f"{TEXT_SECONDARY}", justify="right")

    # Add models to table
    if "models" in models_response:
        # Sort models by name
        models = sorted(models_response["models"], key=lambda x: x.get("model", ""))

        for model in models:
            name = model.get("model", "Unknown")

            # Format size
            size_bytes = model.get("size", 0)
            if size_bytes >= 1_000_000_000:  # GB
                size = f"{size_bytes / 1_000_000_000:.1f} GB"
            elif size_bytes >= 1_000_000:  # MB
                size = f"{size_bytes / 1_000_000:.1f} MB"
            else:
                size = f"{size_bytes / 1_000:.1f} KB"

            table.add_row(name, size)

    console.print(table)
    console.print()

    # Show total count
    total_text = Text()
    total_text.append(f"  Total: ", style=f"dim {TEXT_SECONDARY}")
    model_count = len(models_response.get("models", []))
    total_text.append(
        f"{model_count} model{'s' if model_count != 1 else ''}",
        style=f"{TEXT_SECONDARY}",
    )
    console.print(total_text)
    console.print()


def show_conversations_list(conversation_files: list):
    """Display list of saved conversations"""
    console = Console()

    console.print()

    # Create header
    header = Text()
    header.append("  Saved Conversations", style=f"bold {BRAND_COLOR}")
    console.print(header)
    console.print()

    if not conversation_files:
        # No conversations found
        no_conv_text = Text()
        no_conv_text.append(
            "  No saved conversations found.", style=f"dim {TEXT_SECONDARY}"
        )
        console.print(no_conv_text)
        console.print()
        return

    # Create table
    table = Table(
        show_header=True,
        header_style=f"bold {BRAND_COLOR}",
        border_style=f"dim {TEXT_SECONDARY}",
        box=box.ROUNDED,
        padding=(0, 1),
    )

    table.add_column("Filename", style=f"{TEXT_PRIMARY}", no_wrap=False)
    table.add_column("Size", style=f"{TEXT_SECONDARY}", justify="right")
    table.add_column("Modified", style=f"{TEXT_SECONDARY}")

    # Sort conversations by modified date (newest first)
    conversations = sorted(
        conversation_files, key=lambda x: x["modified"], reverse=True
    )

    for conv in conversations:
        name = conv["name"]

        # Format size
        size_bytes = conv["size"]
        if size_bytes >= 1_000_000:  # MB
            size = f"{size_bytes / 1_000_000:.1f} MB"
        elif size_bytes >= 1_000:  # KB
            size = f"{size_bytes / 1_000:.1f} KB"
        else:
            size = f"{size_bytes} B"

        # Format modified date
        modified_timestamp = conv["modified"]
        dt = datetime.fromtimestamp(modified_timestamp)
        modified = dt.strftime("%Y-%m-%d %H:%M:%S")

        table.add_row(name, size, modified)

    console.print(table)
    console.print()

    # Show total count and usage hint
    total_text = Text()
    total_text.append(f"  Total: ", style=f"dim {TEXT_SECONDARY}")
    conv_count = len(conversation_files)
    total_text.append(
        f"{conv_count} conversation{'s' if conv_count != 1 else ''}",
        style=f"{TEXT_SECONDARY}",
    )
    console.print(total_text)

    # Usage hint
    hint_text = Text()
    hint_text.append("  Tip: Use ", style=f"dim {TEXT_SECONDARY}")
    hint_text.append("/load <filename>", style=f"{ACCENT_COLOR}")
    hint_text.append(" to load a conversation", style=f"dim {TEXT_SECONDARY}")
    console.print(hint_text)
    console.print()


def show_info(message: str):
    """Display an info message"""
    console = Console()
    console.print()

    info_text = Text()
    info_text.append("  ℹ️  ", style=f"bold {BRAND_COLOR}")
    info_text.append(message, style=f"{TEXT_PRIMARY}")

    console.print(info_text)
    console.print()


def show_success(message: str):
    """Display a success message"""
    console = Console()
    console.print()

    success_text = Text()
    success_text.append("  ✅ ", style=f"bold {SUCCESS_COLOR}")
    success_text.append(message, style=f"{TEXT_PRIMARY}")

    console.print(success_text)
    console.print()


def show_reprompting_change(reprompting_enabled: bool):
    """Display reprompting mode status change confirmation"""
    console = Console()
    reprompting_text = Text()
    reprompting_text.append("  ✓ ", style=f"{SUCCESS_COLOR}")

    if reprompting_enabled:
        reprompting_text.append("Reprompting mode ", style=f"{TEXT_SECONDARY}")
        reprompting_text.append("enabled", style=f"bold {SUCCESS_COLOR}")
        reprompting_text.append(" ✨", style=f"{SUCCESS_COLOR}")
        console.print()
        console.print(reprompting_text)
        console.print()
        info_text = Text()
        info_text.append("  ℹ️  ", style=f"{TEXT_SECONDARY}")
        info_text.append(
            "Your messages will be automatically rewritten for better LLM comprehension",
            style=f"dim {TEXT_SECONDARY}",
        )
        console.print(info_text)
    else:
        reprompting_text.append("Reprompting mode ", style=f"{TEXT_SECONDARY}")
        reprompting_text.append("disabled", style=f"bold {TEXT_SECONDARY}")
        reprompting_text.append(" ✨", style=f"{TEXT_SECONDARY}")
        console.print()
        console.print(reprompting_text)

    console.print()


def show_reprompting_animation(content: str, live: Live, start_time: float):
    """Display reprompting animation with token counter"""
    elapsed = time.time() - start_time

    # Animated sparkles with different phases
    sparkle_cycle = int((elapsed * 4) % 3)
    if sparkle_cycle == 0:
        sparkle_char = "✨"
    elif sparkle_cycle == 1:
        sparkle_char = "🌟"
    else:
        sparkle_char = "⭐"

    # Create animated text
    reprompt_text = Text()
    reprompt_text.append("  ", style="")
    reprompt_text.append(sparkle_char, style=f"{WARNING_COLOR}")
    reprompt_text.append(" Reprompting", style=f"bold {TEXT_PRIMARY}")

    # Animated dots
    dots = "." * (int(elapsed * 2) % 4)
    reprompt_text.append(dots.ljust(3), style=f"dim {TEXT_SECONDARY}")

    # Time elapsed
    reprompt_text.append(f" {elapsed:.1f}s", style=f"dim {TEXT_SECONDARY}")

    # Token count (approximate: 4 chars per token)
    if len(content) > 0:
        token_count = get_token_count(content)
        reprompt_text.append(f" · {token_count} tokens", style=f"{WARNING_COLOR}")

    # Preview of content (last 100 chars)
    if len(content) > 0:
        preview = content[-100:] if len(content) > 100 else content
        preview = preview.replace("\n", " ")

        reprompt_text.append("\n  ", style="")
        reprompt_text.append("💭 ", style=f"dim {TEXT_SECONDARY}")
        reprompt_text.append(preview, style=f"italic dim {TEXT_SECONDARY}")

    live.update(reprompt_text)


def show_reprompted_message(
    original: str, reprompted: str, tokens: int = 0, elapsed_time: float = 0.0
):
    """Display the original and reprompted messages side by side with token info"""
    console = Console()
    console.print()

    # Header with token and time info
    header = Text()
    header.append("  ✨ ", style=f"{WARNING_COLOR}")
    header.append("Message reprompted for better clarity", style=f"bold {TEXT_PRIMARY}")
    if tokens > 0:
        header.append(
            f" ({tokens} tokens, {elapsed_time:.2f}s)", style=f"dim {TEXT_SECONDARY}"
        )
    console.print(header)
    console.print()

    # Original message
    original_panel = Panel(
        Text(original, style=f"dim {TEXT_SECONDARY}"),
        title="[dim]Original[/dim]",
        border_style=f"dim {TEXT_SECONDARY}",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(original_panel)

    # Arrow indicator
    arrow = Text()
    arrow.append("  ⬇️  ", style=f"{WARNING_COLOR}")
    console.print(arrow)

    # Reprompted message
    reprompted_panel = Panel(
        Text(reprompted, style=f"{TEXT_PRIMARY}"),
        title="[bold]Optimized[/bold]",
        border_style=f"{WARNING_COLOR}",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(reprompted_panel)

    # Stats footer
    if tokens > 0:
        stats_text = Text()
        stats_text.append("  📊 ", style=f"dim {TEXT_SECONDARY}")
        stats_text.append(f"Reprompting cost: ", style=f"dim {TEXT_SECONDARY}")
        stats_text.append(f"{tokens} tokens", style=f"{WARNING_COLOR}")
        stats_text.append(f" in ", style=f"dim {TEXT_SECONDARY}")
        stats_text.append(f"{elapsed_time:.2f}s", style=f"{TEXT_SECONDARY}")
        console.print(stats_text)

    console.print()
