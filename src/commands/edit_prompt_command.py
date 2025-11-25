"""
Edit Prompt command - Modify the current system prompt
"""

import os
import tempfile
import subprocess
from rich.console import Console
from rich.prompt import Confirm
from .base import Command
from .. import ui


class EditPromptCommand(Command):
    """Edit the current system prompt"""

    def __init__(self):
        super().__init__(
            name="edit-prompt",
            description="Edit the current system prompt (opens in $EDITOR)",
            usage="/edit-prompt [--save]",
        )

    def execute(self, chatbot, args):
        console = Console()
        console.print()

        # Get the current system prompt
        current_prompt = chatbot.model.system_prompt

        if not current_prompt:
            ui.show_error("No system prompt configured for this model")
            return None

        # Determine editor to use
        editor = os.environ.get("EDITOR", "nano")

        # Create a temporary file with the current prompt
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as tmp_file:
            tmp_file.write(current_prompt)
            tmp_path = tmp_file.name

        try:
            # Open the editor
            ui.show_info(f"Opening system prompt in {editor}...")
            console.print()

            # Run the editor
            subprocess.run([editor, tmp_path], check=True)

            # Read the modified content
            with open(tmp_path, "r") as f:
                new_prompt = f.read()

            # Check if there are changes
            if new_prompt.strip() == current_prompt.strip():
                ui.show_warning("No changes made to system prompt")
                return None

            # Show diff statistics
            old_tokens = ui.get_token_count(current_prompt)
            new_tokens = ui.get_token_count(new_prompt)
            token_diff = new_tokens - old_tokens
            diff_sign = "+" if token_diff > 0 else ""

            console.print()
            console.print(
                f"  [dim #9CA3AF]📊 Changes:[/dim #9CA3AF] "
                f"[#E5E7EB]{old_tokens} → {new_tokens} tokens[/#E5E7EB] "
                f"[{'#10B981' if token_diff <= 0 else '#F59E0B'}]({diff_sign}{token_diff})[/{'#10B981' if token_diff <= 0 else '#F59E0B'}]"
            )
            console.print()

            # Confirm changes
            if not Confirm.ask(
                "  [bold #3B82F6]Apply changes to current session?[/bold #3B82F6]",
                default=True,
            ):
                ui.show_warning("Changes discarded")
                return None

            # Apply changes to current model instance (session only)
            chatbot.model.system_prompt = new_prompt

            # Update the system message in conversation history
            if (
                chatbot.conversation_history
                and chatbot.conversation_history[0].get("role") == "system"
            ):
                chatbot.conversation_history[0] = chatbot.model.get_system_prompt()
            else:
                # Insert at the beginning if not present
                chatbot.conversation_history.insert(
                    0, chatbot.model.get_system_prompt()
                )

            ui.show_success(
                "System prompt updated for current session (changes will be lost on restart)"
            )

            # Ask if user wants to save to config file
            console.print()
            if "--save" in args or Confirm.ask(
                "  [bold #F59E0B]Save to models_config.yaml?[/bold #F59E0B]",
                default=False,
            ):
                self._save_to_config(chatbot.model.name, new_prompt)

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return None

    def _save_to_config(self, model_name, new_prompt):
        """Save the new prompt to the models_config.yaml file"""
        import yaml
        from ..utils.paths import get_models_config_path

        config_path = get_models_config_path()

        try:
            # Read current config
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Update the model's system_prompt (base prompt only, not merged)
            if "models" in config and model_name in config["models"]:
                config["models"][model_name]["system_prompt"] = new_prompt

                # Write back to file
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        width=80,
                    )

                ui.show_success(
                    f"System prompt saved to {config_path} (will persist across restarts)"
                )
            else:
                ui.show_error(f"Model '{model_name}' not found in models_config.yaml")

        except Exception as e:
            ui.show_error(f"Failed to save to config: {e}")
