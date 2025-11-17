"""
Init command - Generate AGENTS.md file
"""

from rich.console import Console
from rich.live import Live
from .base import Command
from .. import ui


class InitCommand(Command):
    """Generate AGENTS.md file with comprehensive project documentation"""

    def __init__(self):
        super().__init__(
            name="init",
            description="Generate AGENTS.md file with project documentation",
            usage="/init"
        )

    def execute(self, chatbot, args):
        console = Console()

        # Show start message
        ui.show_info("🚀 Starting project analysis for AGENTS.md generation...")
        console.print()

        # Create the analysis prompt
        analysis_prompt = """You are tasked with creating a comprehensive AGENTS.md file for this project.

This file will be used by AI assistants (LLMs) to understand the entire project architecture, structure, and conventions.

**Your mission:**
1. Explore the project directory structure thoroughly
2. Identify all key components, modules, and their relationships
3. Document the project architecture, design patterns, and coding conventions
4. Create a clear, structured AGENTS.md file that any LLM can read and understand

**Instructions for exploration:**
- Use `execute_command` tool to run commands like `find`, `tree`, `ls -R`, or `git ls-files` to map the project structure
- Use `read_file` tool to read key files (README, main entry points, configuration files, core modules)
- Analyze the code structure, dependencies, and patterns used
- Identify the technology stack, frameworks, and libraries

**AGENTS.md Structure (you MUST follow this structure):**

```markdown
# Project: [Project Name]

## 🎯 Project Overview
[Brief description of what this project does and its purpose]

## 📁 Project Structure
[Detailed directory tree with explanations of each major directory/file]

## 🏗️ Architecture
[Explanation of the overall architecture, design patterns, and how components interact]

## 🔧 Core Components
[Description of each main component/module with:
- Purpose
- Key files
- Responsibilities
- Dependencies]

## 🛠️ Technology Stack
- **Language**: [Programming language and version]
- **Framework**: [Main framework if any]
- **Key Libraries**: [List of important dependencies]
- **Tools**: [Build tools, package managers, etc.]

## 📝 Coding Conventions
[Document any coding standards, naming conventions, or patterns observed in the codebase]

## 🔗 File Relationships
[Explain how files/modules import and depend on each other]

## 🚀 Entry Points
[Main entry points of the application and how to run it]

## 📦 Dependencies & Configuration
[Key configuration files, environment variables, and how dependencies are managed]

## 💡 Important Notes for AI Assistants
[Any specific guidelines, gotchas, or important context that an AI should know when working with this codebase]

## 📚 Functions & Code Map
**CRITICAL: This section prevents code duplication when an LLM works on this project.**

For each module/file in the codebase, list all available functions, classes, and methods with their exact location.
This allows the LLM to quickly find existing functionality and avoid reimplementing code.

Format:
```
### [Module/File Path]
- `function_name(args)` - Line X - [Brief description of what it does]
- `ClassName` - Line Y - [Brief description]
  - `ClassName.method_name(args)` - Line Z - [Brief description]
```

Example:
```
### src/utils/helpers.py
- `parse_config(config_path: str) -> dict` - Line 15 - Parses YAML configuration files
- `validate_input(data: str) -> bool` - Line 42 - Validates user input against schema
- `FileHandler` - Line 67 - Handles file operations
  - `FileHandler.read(path: str) -> str` - Line 71 - Reads file content
  - `FileHandler.write(path: str, content: str)` - Line 89 - Writes content to file

### src/models/base.py
- `BaseModel` - Line 10 - Abstract base class for all models
  - `BaseModel.process(input)` - Line 25 - Process input through the model
  - `BaseModel.validate()` - Line 58 - Validates model configuration
```

**Why this matters:**
- When an LLM needs to add functionality, it can first check this map to see if similar code exists
- Prevents duplicate implementations of the same logic
- Enables code reuse and maintains DRY principles
- Helps the LLM understand what utilities are already available
```

**Now, begin your exploration and create the AGENTS.md file.**
Use the tools available to you (execute_command, read_file, write_file) to explore the project and write a comprehensive AGENTS.md file in the current directory.

Be thorough, precise, and ensure the documentation is clear enough that any LLM reading it can understand the entire project structure without needing to explore the codebase themselves.

**IMPORTANT: You MUST include the "Functions & Code Map" section with a complete inventory of all functions, classes, and methods with their line numbers and locations. This is critical to prevent code duplication.**"""

        try:
            # Create a temporary conversation with the analysis prompt
            temp_history = [chatbot.model.get_system_prompt()]
            temp_message = chatbot.model.get_user_message(analysis_prompt)
            temp_history.append(temp_message)

            # Process the analysis with live display
            with Live(console=console, refresh_per_second=10, transient=False) as live:
                response, elapsed, thinking_content = chatbot.model.process_message(
                    temp_history,
                    live,
                    temperature=0.1,  # Low temperature for more focused analysis
                    enable_thinking=chatbot.enable_thinking
                )

            # Show completion
            console.print()
            ui.show_success("✅ AGENTS.md file generation completed!")
            console.print()
            ui.show_response(console, elapsed, response, thinking_content)

        except Exception as e:
            ui.show_error(f"Failed to generate AGENTS.md: {str(e)}")

        return None
