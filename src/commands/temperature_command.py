"""
Temperature command - Set model temperature
"""

from .base import Command
from .. import ui


class TemperatureCommand(Command):
    """Set the model temperature"""

    def __init__(self):
        super().__init__(
            name="temperature",
            description="Set the model temperature (0.0 to 2.0)",
            usage="/temperature <value>",
        )

    def execute(self, chatbot, args):
        if not args:
            ui.show_error(
                f"Current temperature: {chatbot.temperature}\nUsage: /temperature <value> (0.0 to 2.0)"
            )
            return None

        try:
            new_temp = float(args[0])
            if not 0.0 <= new_temp <= 2.0:
                ui.show_error("Temperature must be between 0.0 and 2.0")
                return None

            chatbot.temperature = new_temp
            ui.show_temperature_change(new_temp)
        except ValueError:
            ui.show_error("Temperature must be a number")

        return None
