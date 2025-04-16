"""Core utility functions for the PM tool."""

import re
import unicodedata
from typing import Optional  # Added for find_project_root


def generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a string.

    Handles lowercasing, replacing spaces/underscores with hyphens,
    removing invalid characters, and collapsing multiple hyphens.
    """
    if not name:
        return ""

    # Normalize unicode characters
    name = unicodedata.normalize('NFKD', name).encode(
        'ascii', 'ignore').decode('ascii')

    # Lowercase and replace spaces/underscores with hyphens
    name = name.lower().replace(' ', '-').replace('_', '-')

    # Remove characters that are not alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]+', '', name)

    # Collapse consecutive hyphens into one
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Ensure slug is not empty after processing
    if not slug:
        # Fallback for names that become empty after slugification
        # (e.g., names consisting only of special characters)
        # A more robust solution might involve using a default or random slug
        return "untitled"

    return slug


def find_project_root() -> Optional[str]:
    """
    Search upwards from the current directory to find the project root
    marked by a '.pm' directory.

    Returns the path (as a string) to the root directory if found, otherwise None.
    """
    # Use pathlib for more modern path handling
    # Local import to avoid potential top-level issues if utils is imported early
    from pathlib import Path

    current_dir = Path.cwd().resolve()  # Start with resolved absolute path
    while True:
        pm_dir_path = current_dir / '.pm'
        if pm_dir_path.is_dir():
            # Return as string to match original signature
            return str(current_dir)

        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            # Reached the filesystem root
            return None
        current_dir = parent_dir
