"""Core utility functions for the PM tool."""

import re
import unicodedata


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
