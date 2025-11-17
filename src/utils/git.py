"""
Git utilities for Claudette
"""

import subprocess


def get_git_branch() -> str | None:
    """
    Get the current git branch name.

    Returns:
        The current branch name or None if not in a git repository
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=1,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None
