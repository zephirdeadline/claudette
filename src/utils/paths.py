"""
XDG Base Directory specification compliant path management for Claudette

This module follows the XDG Base Directory Specification:
https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

Directory hierarchy:
- XDG_CONFIG_HOME (~/.config/claudette/): User configuration files
- XDG_DATA_HOME (~/.local/share/claudette/): User data files
- Project local (.claudette/): Project-specific overrides
"""

import os
from pathlib import Path
from typing import Optional


class ClaudettePaths:
    """
    Manages all file paths for Claudette following XDG standards

    Configuration hierarchy (in order of precedence):
    1. .claudette/ (project-local config - highest priority)
    2. ~/.config/claudette/ (user config)
    3. /etc/claudette/ (system-wide config - lowest priority)

    Data storage:
    - ~/.local/share/claudette/ (user data)
    """

    def __init__(self):
        """Initialize path manager with XDG-compliant directories"""
        # XDG Base Directories
        self.xdg_config_home = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
        self.xdg_data_home = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )

        # Claudette directories
        self.config_dir = self.xdg_config_home / "claudette"
        self.data_dir = self.xdg_data_home / "claudette"
        self.local_config_dir = Path(".claudette")
        self.system_config_dir = Path("/etc/claudette")

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.data_dir / "conversations").mkdir(exist_ok=True)

    def get_config_file(self, filename: str) -> Path:
        """
        Get configuration file path following hierarchy

        Search order:
        1. .claudette/{filename} (project-local)
        2. ~/.config/claudette/{filename} (user)
        3. /etc/claudette/{filename} (system)

        Args:
            filename: Configuration file name

        Returns:
            Path to the configuration file (first found in hierarchy)
        """
        search_paths = [
            self.local_config_dir / filename,
            self.config_dir / filename,
            self.system_config_dir / filename,
        ]

        for path in search_paths:
            if path.exists():
                return path

        # If not found, return user config path (will be created)
        return self.config_dir / filename

    def get_data_file(self, filename: str) -> Path:
        """
        Get data file path (always in user data directory)

        Args:
            filename: Data file name

        Returns:
            Path in ~/.local/share/claudette/
        """
        return self.data_dir / filename

    def get_models_config(self) -> Path:
        """Get models configuration file path"""
        return self.get_config_file("models_config.yaml")

    def get_history_file(self) -> Path:
        """Get command history file path"""
        return self.get_data_file("history.txt")

    def get_stats_file(self) -> Path:
        """Get statistics file path"""
        return self.get_data_file("stats.yaml")

    def get_conversations_dir(self) -> Path:
        """Get conversations directory path"""
        return self.data_dir / "conversations"

    def get_conversation_file(self, name: str) -> Path:
        """
        Get conversation file path

        Args:
            name: Conversation name (without extension)

        Returns:
            Full path to conversation file
        """
        if not name.endswith(".yaml"):
            name += ".yaml"
        return self.get_conversations_dir() / name

    def migrate_from_legacy(self) -> bool:
        """
        Migrate from old ~/.claudette/ structure to XDG-compliant paths

        Returns:
            True if migration was performed, False otherwise
        """
        legacy_dir = Path.home() / ".claudette"

        if not legacy_dir.exists():
            return False

        print("🔄 Migrating from legacy ~/.claudette/ to XDG paths...")

        # Migration mapping
        migrations = [
            (legacy_dir / "models_config.yaml", self.config_dir / "models_config.yaml"),
            (legacy_dir / "claudette_history.txt", self.data_dir / "history.txt"),
            (legacy_dir / "stats.yaml", self.data_dir / "stats.yaml"),
            (legacy_dir / "conversations", self.data_dir / "conversations"),
        ]

        migrated = False
        for source, dest in migrations:
            if source.exists() and not dest.exists():
                print(f"  • {source} → {dest}")
                if source.is_dir():
                    import shutil
                    shutil.copytree(source, dest)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(source, dest)
                migrated = True

        if migrated:
            print("✅ Migration complete!")
            print(f"💡 You can safely remove {legacy_dir} if no other apps use it")

        return migrated


# Singleton instance
_paths_instance: Optional[ClaudettePaths] = None


def get_paths() -> ClaudettePaths:
    """
    Get singleton instance of ClaudettePaths

    Returns:
        ClaudettePaths instance
    """
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = ClaudettePaths()
    return _paths_instance


# Convenience functions for quick access
def get_config_dir() -> Path:
    """Get configuration directory"""
    return get_paths().config_dir


def get_data_dir() -> Path:
    """Get data directory"""
    return get_paths().data_dir


def get_models_config_path() -> Path:
    """Get models configuration file path"""
    return get_paths().get_models_config()


def get_history_path() -> Path:
    """Get history file path"""
    return get_paths().get_history_file()


def get_stats_path() -> Path:
    """Get stats file path"""
    return get_paths().get_stats_file()


def get_conversations_dir() -> Path:
    """Get conversations directory path"""
    return get_paths().get_conversations_dir()
