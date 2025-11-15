"""
Image processing utilities for Claudette
"""

import re
import base64
from pathlib import Path
from typing import List


def extract_and_validate_images(text: str) -> List[str]:
    """
    Extract and validate image paths from text

    Args:
        text: Text containing potential image paths

    Returns:
        List of base64 encoded images
    """
    # Pattern for file paths
    pattern = r'(?:^|\s)([./~]?[^\s]*\.(?:jpg|jpeg|png|gif|bmp|webp))(?:\s|$)'

    potential_paths = re.findall(pattern, text, re.IGNORECASE)

    valid_images = []

    for path_str in potential_paths:
        path = Path(path_str).expanduser()  # Handle ~/

        # Validations
        if path.exists() and path.is_file():
            # Verify it's an image
            if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                valid_images.append(image_to_base64(str(path.absolute())))

    return valid_images


def image_to_base64(image_path: str) -> str:
    """
    Convert an image to base64 encoding

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded
