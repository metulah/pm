# pm/cli/guideline/utils.py
import frontmatter
from pathlib import Path
from typing import Union

# import re  # No longer needed
# Adjust relative import path to access constants from the parent directory
# Import from the new core location
from pm.core.constants import RESOURCES_DIR

# Note: Custom guidelines directory is determined dynamically within functions using Path.cwd()

# --- Helper Functions ---


def _ensure_custom_dir():
    """Ensures the custom guidelines directory exists based on CWD."""
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    custom_dir.mkdir(parents=True, exist_ok=True)
    return custom_dir  # Return the path for potential reuse


def _resolve_guideline_path(name: str) -> tuple[Union[Path, None], Union[str, None]]:
    """
    Resolves the path to a guideline, checking custom dir first, then built-in.
    Uses Path.cwd() to determine the custom directory location dynamically.
    Returns (path, type) where type is 'Custom' or 'Built-in', or (None, None).
    """
    # Check custom guidelines first
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    custom_path = custom_dir / f"{name}.md"
    if custom_path.is_file():
        return custom_path, "Custom"

    # Check built-in guidelines
    builtin_filename = f"welcome_guidelines_{name}.md"
    builtin_path = RESOURCES_DIR / builtin_filename
    if builtin_path.is_file():
        return builtin_path, "Built-in"

    return None, None


def _read_content_input(content_input: Union[str, None]) -> Union[str, None]:
    """
    Reads content, handling inline text or '@<path>' syntax.
    Returns the content string or None if input is None.
    Raises FileNotFoundError or other IOErrors if '@<path>' fails.
    """
    if content_input is None:
        return None
    if content_input.startswith("@"):
        file_path_str = content_input[1:]
        # Resolve relative to CWD
        file_path = Path.cwd() / file_path_str
        if not file_path.is_file():
            raise FileNotFoundError(f"File specified by '@' not found: {file_path}")
        # Read with UTF-8 encoding
        return file_path.read_text(encoding="utf-8")
    else:
        return content_input


def _write_guideline(path: Path, content: str, metadata: Union[dict, None] = None):
    """Writes guideline content and metadata using frontmatter."""
    # Create the Post object with the direct metadata
    post = frontmatter.Post(content=content, metadata=metadata or {})
    # Ensure the directory exists before writing
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        # Use dumps to get string, then write to text file handle
        f.write(frontmatter.dumps(post))


# --- discover_available_guidelines function removed (redundant) ---
# Use pm.core.guideline.get_available_guidelines instead.


# --- End Helper Functions ---
