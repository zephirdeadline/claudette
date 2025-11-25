"""
List Directory Tool - List contents of a directory
"""

import os
from pathlib import Path
from .base import Tool


class ListDirectoryTool(Tool):
    """List directory contents with detailed information"""

    def __init__(self):
        super().__init__(
            name="list_directory",
            description="List contents of a directory with detailed information about files and subdirectories",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list (absolute or relative). Defaults to current working directory if not specified.",
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files (files starting with .). Default: false",
                        "default": False,
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list subdirectories recursively. Default: false",
                        "default": False,
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth for recursive listing. Default: 3",
                        "default": 3,
                    },
                },
                "required": [],
            },
        )

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def _list_directory_simple(self, path: str, show_hidden: bool) -> str:
        """List directory contents in simple mode (non-recursive)"""
        try:
            target_path = Path(path).resolve()

            if not target_path.exists():
                return f"Error: Path does not exist: {path}"

            if not target_path.is_dir():
                return f"Error: Path is not a directory: {path}"

            # Get all entries
            entries = []
            try:
                for entry in sorted(
                    target_path.iterdir(),
                    key=lambda x: (not x.is_dir(), x.name.lower()),
                ):
                    # Skip hidden files if not requested
                    if not show_hidden and entry.name.startswith("."):
                        continue

                    # Get entry info
                    is_dir = entry.is_dir()
                    try:
                        size = entry.stat().st_size if not is_dir else 0
                        size_str = self._format_size(size) if not is_dir else "<DIR>"
                    except (OSError, PermissionError):
                        size_str = "<N/A>"

                    # Format entry
                    icon = "📁" if is_dir else "📄"
                    entries.append(f"{icon} {entry.name:<50} {size_str:>10}")

            except PermissionError:
                return f"Error: Permission denied to access directory: {path}"

            # Build result
            result = []
            result.append(f"Directory: {target_path}")
            result.append(f"{'=' * 80}")

            if not entries:
                result.append("(empty directory)")
            else:
                result.append(f"{'Name':<53} {'Size':>10}")
                result.append(f"{'-' * 80}")
                result.extend(entries)

                # Summary
                dirs_count = sum(
                    1
                    for e in target_path.iterdir()
                    if e.is_dir() and (show_hidden or not e.name.startswith("."))
                )
                files_count = sum(
                    1
                    for e in target_path.iterdir()
                    if e.is_file() and (show_hidden or not e.name.startswith("."))
                )
                result.append(f"{'-' * 80}")
                result.append(
                    f"Total: {dirs_count} director{'ies' if dirs_count != 1 else 'y'}, {files_count} file{'s' if files_count != 1 else ''}"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def _list_directory_recursive(
        self,
        path: str,
        show_hidden: bool,
        max_depth: int,
        current_depth: int = 0,
        prefix: str = "",
    ) -> list:
        """List directory contents recursively"""
        if current_depth >= max_depth:
            return []

        try:
            target_path = Path(path).resolve()

            if not target_path.exists() or not target_path.is_dir():
                return []

            results = []
            entries = []

            # Get all entries
            try:
                for entry in sorted(
                    target_path.iterdir(),
                    key=lambda x: (not x.is_dir(), x.name.lower()),
                ):
                    # Skip hidden files if not requested
                    if not show_hidden and entry.name.startswith("."):
                        continue
                    entries.append(entry)
            except PermissionError:
                results.append(f"{prefix}[Permission Denied]")
                return results

            # Process entries
            for idx, entry in enumerate(entries):
                is_last = idx == len(entries) - 1
                connector = "└── " if is_last else "├── "

                is_dir = entry.is_dir()
                icon = "📁" if is_dir else "📄"

                # Get size info
                try:
                    size = entry.stat().st_size if not is_dir else 0
                    size_str = f" ({self._format_size(size)})" if not is_dir else ""
                except (OSError, PermissionError):
                    size_str = " (N/A)"

                results.append(f"{prefix}{connector}{icon} {entry.name}{size_str}")

                # Recursively list subdirectories
                if is_dir:
                    extension = "    " if is_last else "│   "
                    sub_results = self._list_directory_recursive(
                        str(entry),
                        show_hidden,
                        max_depth,
                        current_depth + 1,
                        prefix + extension,
                    )
                    results.extend(sub_results)

            return results

        except Exception as e:
            return [f"{prefix}[Error: {str(e)}]"]

    def execute(
        self,
        path: str = ".",
        show_hidden: bool = False,
        recursive: bool = False,
        max_depth: int = 3,
    ) -> str:
        """
        List directory contents

        Args:
            path: Directory path to list
            show_hidden: Whether to show hidden files
            recursive: Whether to list recursively
            max_depth: Maximum depth for recursive listing

        Returns:
            Formatted directory listing
        """
        try:
            # Convert parameters to correct types (in case they come as strings from API)
            show_hidden = (
                bool(show_hidden)
                if isinstance(show_hidden, bool)
                else show_hidden == "true"
            )
            recursive = (
                bool(recursive) if isinstance(recursive, bool) else recursive == "true"
            )
            max_depth = int(max_depth) if not isinstance(max_depth, int) else max_depth

            # Resolve path
            target_path = Path(path).resolve()

            if recursive:
                # Recursive tree view
                result = []
                result.append(f"Directory Tree: {target_path}")
                result.append(f"{'=' * 80}")
                result.append(f"📁 {target_path.name or str(target_path)}")

                tree_lines = self._list_directory_recursive(
                    str(target_path), show_hidden, max_depth
                )
                result.extend(tree_lines)

                result.append(f"{'=' * 80}")
                result.append(f"Max depth: {max_depth} levels")

                return "\n".join(result)
            else:
                # Simple flat listing
                return self._list_directory_simple(str(target_path), show_hidden)

        except Exception as e:
            return f"Error: {str(e)}"
