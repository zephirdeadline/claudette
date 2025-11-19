"""
Stats Command - Display usage statistics
"""

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .base import Command
from ..utils import StatsManager


class StatsCommand(Command):
    """Display usage statistics for all models"""

    def __init__(self):
        super().__init__(
            name="stats",
            description="Display usage statistics per model",
            usage="/stats [model_name]",
        )

    def execute(self, chatbot: "ChatBot", args: list[str]) -> str | None:
        """Execute the stats command"""
        stats_manager = StatsManager()

        # If a specific model is requested
        if args:
            model_name = " ".join(args)
            stats = stats_manager.get_stats(model_name)

            if not stats:
                console = Console()
                console.print()
                error_text = Text()
                error_text.append("  ⚠️ ", style="bold #EF4444")
                error_text.append(
                    f"No statistics found for model: {model_name}", style="#E5E7EB"
                )
                console.print(error_text)
                console.print()
                return None

            self._display_single_model_stats(model_name, stats)
        else:
            # Display all models
            all_stats = stats_manager.get_stats()

            if not all_stats:
                console = Console()
                console.print()
                info_text = Text()
                info_text.append("  ℹ️  ", style="bold #3B82F6")
                info_text.append(
                    "No statistics available yet. Start chatting to generate stats!",
                    style="#E5E7EB",
                )
                console.print(info_text)
                console.print()
                return None

            self._display_all_models_stats(all_stats)

        return None

    def _display_single_model_stats(self, model_name: str, stats: dict):
        """Display statistics for a single model"""
        console = Console()
        console.print()

        # Header
        header_text = Text()
        header_text.append("  📊 ", style="bold #3B82F6")
        header_text.append(f"Statistics for {model_name}", style="bold #E5E7EB")
        console.print(header_text)
        console.print()

        # Stats details
        thinking_tokens = stats.get("total_thinking_tokens", 0)
        response_tokens = stats.get("total_response_tokens", 0)
        total_tokens = thinking_tokens + response_tokens
        total_time = stats.get("total_time_seconds", 0.0)
        total_requests = stats.get("total_requests", 0)

        # Reprompting stats
        reprompting_tokens = stats.get("reprompting_tokens", 0)
        reprompting_requests = stats.get("reprompting_requests", 0)
        reprompting_time = stats.get("reprompting_time_seconds", 0.0)

        # Calculate averages
        avg_thinking_tokens = (
            thinking_tokens / total_requests if total_requests > 0 else 0
        )
        avg_response_tokens = (
            response_tokens / total_requests if total_requests > 0 else 0
        )
        avg_total_tokens = total_tokens / total_requests if total_requests > 0 else 0
        avg_time = total_time / total_requests if total_requests > 0 else 0

        # Format time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        time_str = (
            f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"
        )

        console.print(f"  Total Requests: [bold #10B981]{total_requests}[/]")
        console.print(f"  Total Thinking Tokens: [bold #F59E0B]{thinking_tokens:,}[/]")
        console.print(f"  Total Response Tokens: [bold #3B82F6]{response_tokens:,}[/]")
        console.print(f"  Total Tokens: [bold #8B5CF6]{total_tokens:,}[/]")
        console.print(f"  Total Time: [bold #EC4899]{time_str}[/]")
        console.print()

        # Reprompting section
        if reprompting_requests > 0:
            console.print(f"  [dim #9CA3AF]Reprompting Statistics:[/]")
            console.print(
                f"  Reprompting Requests: [bold #F59E0B]{reprompting_requests}[/]"
            )
            console.print(
                f"  Reprompting Tokens: [bold #F59E0B]{reprompting_tokens:,}[/]"
            )
            console.print(
                f"  Reprompting Time: [bold #F59E0B]{reprompting_time:.2f}s[/]"
            )
            console.print(
                f"  Avg Tokens/Reprompt: [bold #F59E0B]{reprompting_tokens / reprompting_requests:.1f}[/]"
            )
            console.print()

        console.print(
            f"  Avg Thinking Tokens/Request: [bold #F59E0B]{avg_thinking_tokens:,.1f}[/]"
        )
        console.print(
            f"  Avg Response Tokens/Request: [bold #3B82F6]{avg_response_tokens:,.1f}[/]"
        )
        console.print(
            f"  Avg Total Tokens/Request: [bold #8B5CF6]{avg_total_tokens:,.1f}[/]"
        )
        console.print(f"  Avg Time/Request: [bold #EC4899]{avg_time:.2f}s[/]")
        console.print()

    def _display_all_models_stats(self, all_stats: dict):
        """Display statistics for all models in a table"""
        console = Console()
        console.print()

        # Header
        header_text = Text()
        header_text.append("  📊 ", style="bold #3B82F6")
        header_text.append("Usage Statistics", style="bold #E5E7EB")
        console.print(header_text)
        console.print()

        # Create table
        table = Table(
            show_header=True, header_style="bold #3B82F6", border_style="#374151"
        )
        table.add_column("Model", style="#E5E7EB", no_wrap=True)
        table.add_column("Requests", justify="right", style="#10B981")
        table.add_column("Think Tokens", justify="right", style="#F59E0B")
        table.add_column("Resp Tokens", justify="right", style="#3B82F6")
        table.add_column("Total Tokens", justify="right", style="#8B5CF6")
        table.add_column("Reprompt", justify="right", style="#F59E0B")
        table.add_column("Total Time", justify="right", style="#EC4899")

        # Add rows for each model
        for model_name, stats in all_stats.items():
            thinking_tokens = stats.get("total_thinking_tokens", 0)
            response_tokens = stats.get("total_response_tokens", 0)
            total_tokens = thinking_tokens + response_tokens
            total_time = stats.get("total_time_seconds", 0.0)
            total_requests = stats.get("total_requests", 0)
            reprompting_tokens = stats.get("reprompting_tokens", 0)

            # Format time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = int(total_time % 60)
            time_str = (
                f"{hours}h {minutes}m {seconds}s"
                if hours > 0
                else f"{minutes}m {seconds}s"
            )

            # Format reprompting
            reprompt_str = f"{reprompting_tokens:,}" if reprompting_tokens > 0 else "-"

            table.add_row(
                model_name,
                str(total_requests),
                f"{thinking_tokens:,}",
                f"{response_tokens:,}",
                f"{total_tokens:,}",
                reprompt_str,
                time_str,
            )

        console.print(table)
        console.print()

        # Calculate global statistics
        global_thinking_tokens = 0
        global_response_tokens = 0
        global_reprompting_tokens = 0
        global_total_time = 0.0
        global_reprompting_time = 0.0
        global_requests = 0
        global_reprompting_requests = 0

        for model_name, stats in all_stats.items():
            global_thinking_tokens += stats.get("total_thinking_tokens", 0)
            global_response_tokens += stats.get("total_response_tokens", 0)
            global_reprompting_tokens += stats.get("reprompting_tokens", 0)
            global_total_time += stats.get("total_time_seconds", 0.0)
            global_reprompting_time += stats.get("reprompting_time_seconds", 0.0)
            global_requests += stats.get("total_requests", 0)
            global_reprompting_requests += stats.get("reprompting_requests", 0)

        global_total_tokens = (
            global_thinking_tokens + global_response_tokens + global_reprompting_tokens
        )
        grand_total_time = global_total_time + global_reprompting_time

        # Display global statistics header
        global_header = Text()
        global_header.append("  🌍 ", style="bold #10B981")
        global_header.append("Global Statistics (All Models)", style="bold #E5E7EB")
        console.print(global_header)
        console.print()

        # Display global stats with separators
        console.print(f"  [dim #9CA3AF]─── Thinking ───[/]")
        console.print(
            f"  Total Thinking Tokens: [bold #F59E0B]{global_thinking_tokens:,}[/]"
        )
        console.print()

        console.print(f"  [dim #9CA3AF]─── Response ───[/]")
        console.print(
            f"  Total Response Tokens: [bold #3B82F6]{global_response_tokens:,}[/]"
        )
        console.print()

        if global_reprompting_tokens > 0:
            console.print(f"  [dim #9CA3AF]─── Reprompting ───[/]")
            console.print(
                f"  Total Reprompting Tokens: [bold #F59E0B]{global_reprompting_tokens:,}[/]"
            )
            console.print(
                f"  Total Reprompting Requests: [bold #F59E0B]{global_reprompting_requests}[/]"
            )
            # Format reprompting time
            rep_hours = int(global_reprompting_time // 3600)
            rep_minutes = int((global_reprompting_time % 3600) // 60)
            rep_seconds = int(global_reprompting_time % 60)
            rep_time_str = (
                f"{rep_hours}h {rep_minutes}m {rep_seconds}s"
                if rep_hours > 0
                else f"{rep_minutes}m {rep_seconds}s"
            )
            console.print(f"  Total Reprompting Time: [bold #F59E0B]{rep_time_str}[/]")
            console.print()

        console.print(f"  [dim #9CA3AF]{'═' * 50}[/]")
        console.print()

        # Grand totals
        console.print(
            f"  [bold #8B5CF6]GRAND TOTAL TOKENS:[/] [bold #8B5CF6]{global_total_tokens:,}[/]"
        )
        console.print(
            f"    • Thinking: [#F59E0B]{global_thinking_tokens:,}[/] ([dim]{global_thinking_tokens / global_total_tokens * 100:.1f}%[/])"
        )
        console.print(
            f"    • Response: [#3B82F6]{global_response_tokens:,}[/] ([dim]{global_response_tokens / global_total_tokens * 100:.1f}%[/])"
        )
        if global_reprompting_tokens > 0:
            console.print(
                f"    • Reprompting: [#F59E0B]{global_reprompting_tokens:,}[/] ([dim]{global_reprompting_tokens / global_total_tokens * 100:.1f}%[/])"
            )
        console.print()

        # Format grand total time
        grand_hours = int(grand_total_time // 3600)
        grand_minutes = int((grand_total_time % 3600) // 60)
        grand_seconds = int(grand_total_time % 60)
        grand_time_str = (
            f"{grand_hours}h {grand_minutes}m {grand_seconds}s"
            if grand_hours > 0
            else f"{grand_minutes}m {grand_seconds}s"
        )

        # Format inference time (excluding reprompting)
        inf_hours = int(global_total_time // 3600)
        inf_minutes = int((global_total_time % 3600) // 60)
        inf_seconds = int(global_total_time % 60)
        inf_time_str = (
            f"{inf_hours}h {inf_minutes}m {inf_seconds}s"
            if inf_hours > 0
            else f"{inf_minutes}m {inf_seconds}s"
        )

        console.print(
            f"  [bold #EC4899]GRAND TOTAL TIME:[/] [bold #EC4899]{grand_time_str}[/]"
        )
        console.print(f"    • Inference: [#EC4899]{inf_time_str}[/]")
        if global_reprompting_time > 0:
            console.print(f"    • Reprompting: [#F59E0B]{rep_time_str}[/]")
        console.print()

        # Additional metrics
        console.print(
            f"  [dim #9CA3AF]Total Requests: {global_requests} | Avg Tokens/Request: {global_total_tokens / global_requests:.1f}[/]"
        )
        console.print()
