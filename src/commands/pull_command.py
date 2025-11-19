"""
Pull command - Download a model from Ollama
"""

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from .base import Command
from .. import ui


class PullCommand(Command):
    """Download a model from Ollama"""

    def __init__(self):
        super().__init__(
            name="pull",
            description="Download a model from Ollama",
            usage="/pull <model_name>",
        )

    def execute(self, chatbot, args):
        if not args:
            ui.show_error("Usage: /pull <model_name>")
            return None

        model_name = args[0]
        ui.show_pull_start(model_name)

        try:
            console = Console()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(f"Downloading {model_name}", total=None)

                for chunk in chatbot.model.ollama_client.pull(model_name, stream=True):
                    if "total" in chunk and "completed" in chunk:
                        progress.update(
                            task, total=chunk["total"], completed=chunk["completed"]
                        )
                    elif "status" in chunk:
                        progress.update(task, description=f"{chunk['status']}")

            ui.show_pull_success(model_name)

        except Exception as e:
            ui.show_error(f"Failed to pull model: {e}")

        return None
