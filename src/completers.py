"""
Custom completers for Claudette
"""

import os
from typing import Iterable
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class FilePathCompleter(Completer):
    """
    Completer for file paths triggered by @ symbol.
    Provides recursive autocompletion for all files in the project.
    """

    def __init__(self):
        super().__init__()
        self._file_cache = []
        self._cache_cwd = None

    def _scan_directory_recursive(self, root_dir: str) -> list[tuple[str, str, int]]:
        """
        Recursively scan directory and return all files with their relative paths

        Args:
            root_dir: Root directory to scan

        Returns:
            List of tuples (relative_path, absolute_path, size)
        """
        files = []

        # Common directories to ignore
        ignore_dirs = {
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".env",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "htmlcov",
            ".idea",
            ".vscode",
            "__MACOSX",
            ".DS_Store",
        }

        try:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # Remove ignored directories from the walk
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d not in ignore_dirs and not d.startswith(".")
                ]

                # Calculate relative path from root
                rel_dir = os.path.relpath(dirpath, root_dir)
                if rel_dir == ".":
                    rel_dir = ""

                # Add all files in this directory
                for filename in filenames:
                    # Skip hidden files
                    if filename.startswith("."):
                        continue

                    # Build paths
                    if rel_dir:
                        rel_path = os.path.join(rel_dir, filename)
                    else:
                        rel_path = filename

                    abs_path = os.path.join(dirpath, filename)

                    # Get file size
                    try:
                        size = os.path.getsize(abs_path)
                    except:
                        size = 0

                    files.append((rel_path, abs_path, size))

        except Exception:
            pass

        return files

    def _get_all_files(self, cwd: str) -> list[tuple[str, str, int]]:
        """
        Get all files from cache or scan if needed

        Args:
            cwd: Current working directory

        Returns:
            List of (relative_path, absolute_path, size) tuples
        """
        # Check if we need to refresh cache
        if self._cache_cwd != cwd or not self._file_cache:
            self._file_cache = self._scan_directory_recursive(cwd)
            self._cache_cwd = cwd

        return self._file_cache

    def get_completions(self, document: Document, complete_event):
        """
        Get file completions when @ is detected

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects for matching files
        """
        text = document.text_before_cursor

        # Only trigger completion if there's an @ symbol
        if "@" not in text:
            return

        # Find the last @ position
        last_at_pos = text.rfind("@")

        # Get the text after the last @
        after_at = text[last_at_pos + 1 :]

        # Get current working directory
        try:
            cwd = os.getcwd()

            # Get all files recursively
            all_files = self._get_all_files(cwd)

            # Filter files that match the text after @
            matching_files = []
            for rel_path, abs_path, size in all_files:
                # Check if the relative path matches (case-insensitive)
                if after_at.lower() in rel_path.lower():
                    matching_files.append((rel_path, abs_path, size))

            # Sort by relevance (starts with match first, then contains match)
            def sort_key(item):
                rel_path = item[0]
                # Prioritize matches that start with the search term
                if rel_path.lower().startswith(after_at.lower()):
                    return (0, rel_path.lower())
                # Then basename matches
                basename = os.path.basename(rel_path)
                if basename.lower().startswith(after_at.lower()):
                    return (1, rel_path.lower())
                # Then contains in basename
                if after_at.lower() in basename.lower():
                    return (2, rel_path.lower())
                # Finally, contains anywhere
                return (3, rel_path.lower())

            matching_files.sort(key=sort_key)

            # Yield completions (limit to 50 to avoid overwhelming the user)
            for rel_path, abs_path, size in matching_files[:50]:
                # Format size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"

                # Determine if it's in a subdirectory
                if os.path.sep in rel_path:
                    dir_part = os.path.dirname(rel_path)
                    display_meta = f"📄 {size_str} ({dir_part})"
                else:
                    display_meta = f"📄 {size_str}"

                # Calculate the position to replace everything from @ onwards
                # start_position is negative: how many characters back from cursor to start replacing
                # We want to replace the @ symbol AND everything after it
                start_pos = -(len(after_at) + 1)  # +1 to include the @ symbol

                yield Completion(
                    rel_path, start_position=start_pos, display_meta=display_meta
                )

        except Exception:
            # If any error occurs, don't provide completions
            return


class CommandAndFileCompleter(Completer):
    """
    Combined completer that handles both commands (/) and file paths (@)
    """

    def __init__(self, command_names: list[str]):
        """
        Initialize the combined completer

        Args:
            command_names: List of command names (with / prefix)
        """
        super().__init__()
        self.command_names = command_names
        self.file_completer = FilePathCompleter()

    def get_completions(self, document: Document, complete_event):
        """
        Get completions based on context (command or file)

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor

        # If text starts with /, provide command completions
        if text.startswith("/"):
            # Extract the command part
            words = text.split()
            if len(words) == 0 or (len(words) == 1 and not text.endswith(" ")):
                # Still typing the command
                command_part = text[1:]  # Remove the /
                for cmd in self.command_names:
                    cmd_without_slash = cmd[1:]  # Remove / for comparison
                    if cmd_without_slash.startswith(command_part.lower()):
                        yield Completion(
                            cmd_without_slash,
                            start_position=-len(command_part),
                            display_meta="command",
                        )

        # If text contains @, provide file completions
        elif "@" in text:
            # Delegate to file completer
            yield from self.file_completer.get_completions(document, complete_event)
