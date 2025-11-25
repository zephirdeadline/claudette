"""
Stats Manager - Track token usage and execution time per model
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

from .paths import get_stats_path


class StatsManager:
    """Manage statistics tracking for model usage"""

    def __init__(self):
        """Initialize the stats manager using XDG paths"""
        self.stats_file = get_stats_path()
        self._ensure_stats_file()

    def _ensure_stats_file(self):
        """Ensure the stats file exists"""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.stats_file.exists():
            self._write_stats({})

    def _read_stats(self) -> Dict[str, Any]:
        """Read stats from YAML file"""
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                stats = yaml.safe_load(f)
                return stats if stats else {}
        except Exception:
            return {}

    def _write_stats(self, stats: Dict[str, Any]):
        """Write stats to YAML file"""
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    stats,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except Exception as e:
            print(f"Warning: Failed to write stats: {e}")

    def update_stats(
        self,
        model_name: str,
        thinking_tokens: int,
        response_tokens: int,
        time_seconds: float,
        is_reprompting: bool = False,
    ):
        """
        Update statistics for a model

        Args:
            model_name: Name of the model used
            thinking_tokens: Number of thinking tokens consumed
            response_tokens: Number of response tokens consumed
            time_seconds: Time in seconds for the API call
            is_reprompting: Whether this is a reprompting request
        """
        stats = self._read_stats()

        # Initialize model stats if not exists
        if model_name not in stats:
            stats[model_name] = {
                "total_thinking_tokens": 0,
                "total_response_tokens": 0,
                "total_time_seconds": 0.0,
                "total_requests": 0,
                "reprompting_tokens": 0,
                "reprompting_requests": 0,
                "reprompting_time_seconds": 0.0,
            }

        # Ensure reprompting fields exist for backward compatibility
        if "reprompting_tokens" not in stats[model_name]:
            stats[model_name]["reprompting_tokens"] = 0
        if "reprompting_requests" not in stats[model_name]:
            stats[model_name]["reprompting_requests"] = 0
        if "reprompting_time_seconds" not in stats[model_name]:
            stats[model_name]["reprompting_time_seconds"] = 0.0

        # Update stats
        stats[model_name]["total_thinking_tokens"] += thinking_tokens
        stats[model_name]["total_response_tokens"] += response_tokens
        stats[model_name]["total_time_seconds"] += time_seconds
        stats[model_name]["total_requests"] += 1

        # Track reprompting separately
        if is_reprompting:
            stats[model_name]["reprompting_tokens"] += response_tokens
            stats[model_name]["reprompting_requests"] += 1
            stats[model_name]["reprompting_time_seconds"] += time_seconds

        # Write back to file
        self._write_stats(stats)

    def get_stats(self, model_name: str = None) -> Dict[str, Any]:
        """
        Get statistics for a model or all models

        Args:
            model_name: Optional model name. If None, returns all stats.

        Returns:
            Dictionary with stats
        """
        stats = self._read_stats()
        if model_name:
            return stats.get(model_name, {})
        return stats

    def reset_stats(self, model_name: str = None):
        """
        Reset statistics

        Args:
            model_name: Optional model name. If None, resets all stats.
        """
        if model_name:
            stats = self._read_stats()
            if model_name in stats:
                del stats[model_name]
                self._write_stats(stats)
        else:
            self._write_stats({})
