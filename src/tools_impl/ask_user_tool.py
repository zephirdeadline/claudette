"""
Ask User Tool - Ask the user a question
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory

from .base import Tool


class AskUserTool(Tool):
    """Ask the user a question when clarification is needed"""

    def __init__(self):
        super().__init__(
            name="ask_user",
            description="Ask the user a question when you need clarification or additional information. Use this when you're unsure about something or need the user to make a choice.",
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context explaining why you're asking this question",
                    },
                },
                "required": ["question"],
            },
        )

    def execute(self, question: str, context: str = None) -> str:
        """Ask the user a question and return their response"""
        console = Console()
        console.print()

        # Show the question in a nice panel
        question_text = Text()
        question_text.append("❓ ", style="bold #F59E0B")
        question_text.append("Question from AI", style="bold #E5E7EB")
        console.print(Panel(question_text, border_style="#F59E0B", padding=(0, 1)))

        # Show context if provided
        if context:
            context_text = Text()
            context_text.append("Context: ", style="dim #9CA3AF")
            context_text.append(context, style="#9CA3AF")
            console.print(context_text)
            console.print()

        # Show the question
        q_text = Text()
        q_text.append("  ", style="")
        q_text.append(question, style="bold #E5E7EB")
        console.print(q_text)
        console.print()

        # Get user response with prompt_toolkit for history and navigation
        try:
            session = PromptSession(history=InMemoryHistory())
            response = session.prompt(
                HTML('<ansi color="#9CA3AF">  Your answer: </ansi>')
            ).strip()
            console.print()

            if not response:
                return "User provided no answer."

            return f"User's response: {response}"
        except (EOFError, KeyboardInterrupt):
            console.print()
            return "User cancelled the question."
