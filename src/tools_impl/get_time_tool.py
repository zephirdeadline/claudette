"""
Get Current Time Tool - Retrieve current date and time information
"""

from datetime import datetime
from .base import Tool


class GetCurrentTimeTool(Tool):
    """Tool to get current date and time information"""

    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="Get the current date and time with detailed temporal information. Returns current date, time, day of week, and Unix timestamp.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    def execute(self, **kwargs) -> str:
        """
        Execute the get_current_time tool

        Returns:
            Formatted string with current date and time information
        """
        # Get current date and time
        now = datetime.now()

        # Format different time representations
        full_datetime = now.strftime("%A, %B %d, %Y at %H:%M:%S")
        date_only = now.strftime("%Y-%m-%d")
        time_only = now.strftime("%H:%M:%S")
        day_of_week = now.strftime("%A")
        month_name = now.strftime("%B")
        year = now.strftime("%Y")
        iso_format = now.isoformat()
        unix_timestamp = int(now.timestamp())

        # Build result string
        result = f"""Current Date and Time Information:

Full: {full_datetime}
Date: {date_only}
Time: {time_only}
Day of Week: {day_of_week}
Month: {month_name}
Year: {year}

ISO Format: {iso_format}
Unix Timestamp: {unix_timestamp}

Timezone: System local time"""

        return result
