# pm/cli/guideline/utils.py
import frontmatter
from pathlib import Path
import re  # Added for slug extraction
from typing import List, Dict, Any, Optional  # Added for type hints
# Adjust relative import path to access constants from the parent directory
from ..constants import RESOURCES_DIR

# Note: Custom guidelines directory is determined dynamically within functions using Path.cwd()

# --- Helper Functions ---


def _ensure_custom_dir():
    """Ensures the custom guidelines directory exists based on CWD."""
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    custom_dir.mkdir(parents=True, exist_ok=True)
    return custom_dir  # Return the path for potential reuse


def _resolve_guideline_path(name: str) -> tuple[Path | None, str | None]:
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


def _read_content_input(content_input: str | None) -> str | None:
    """
    Reads content, handling inline text or '@<path>' syntax.
    Returns the content string or None if input is None.
    Raises FileNotFoundError or other IOErrors if '@<path>' fails.
    """
    if content_input is None:
        return None
    if content_input.startswith('@'):
        file_path_str = content_input[1:]
        # Resolve relative to CWD
        file_path = Path.cwd() / file_path_str
        if not file_path.is_file():
            raise FileNotFoundError(
                f"File specified by '@' not found: {file_path}")
        # Read with UTF-8 encoding
        return file_path.read_text(encoding='utf-8')
    else:
        return content_input


def _write_guideline(path: Path, content: str, metadata: dict | None = None):
    """Writes guideline content and metadata using frontmatter."""
    # Create the Post object with the direct metadata
    post = frontmatter.Post(content=content, metadata=metadata or {})
    # Ensure the directory exists before writing
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        # Use dumps to get string, then write to text file handle
        f.write(frontmatter.dumps(post))

# --- New Function for Guideline Discovery ---


def discover_available_guidelines() -> List[Dict[str, Any]]:
    """
    Discovers available built-in guidelines by scanning the resources directory.

    Looks for files matching 'welcome_guidelines_*.md', extracts the slug,
    and attempts to read metadata (like 'title') using frontmatter.

    Returns:
        A list of dictionaries, each representing a guideline with keys
        like 'slug', 'title', 'path'. Returns empty list if none found
        or on error accessing the resources directory.
    """
    discovered: List[Dict[str, Any]] = []
    if not RESOURCES_DIR.is_dir():
        # TODO: Add proper logging/warning
        print(f"Warning: Resources directory not found at {RESOURCES_DIR}")
        return discovered

    # Regex to extract the slug from the filename
    # Matches 'welcome_guidelines_' followed by one or more characters (slug) until '.md'
    pattern = re.compile(r"^welcome_guidelines_(.+)\.md$")

    for item in RESOURCES_DIR.iterdir():
        if item.is_file():
            match = pattern.match(item.name)
            if match:
                slug = match.group(1)
                guideline_info: Dict[str, Any] = {
                    "slug": slug,
                    "path": item,
                    # Default title from slug
                    "title": slug.replace('_', ' ').title(),
                    "description": None  # Default description
                }
                try:
                    # Attempt to load frontmatter to get better title/description
                    post = frontmatter.load(item)
                    if isinstance(post.metadata, dict):
                        # Use title from metadata if present and non-empty string
                        meta_title = post.metadata.get("title")
                        if meta_title and isinstance(meta_title, str):
                            guideline_info["title"] = meta_title.strip()

                        # Use description from metadata if present and non-empty string
                        meta_desc = post.metadata.get("description")
                        if meta_desc and isinstance(meta_desc, str):
                            guideline_info["description"] = meta_desc.strip()

                except Exception as e:
                    # Ignore errors reading frontmatter for discovery, use defaults
                    # TODO: Add proper logging/warning
                    print(
                        f"Warning: Could not parse frontmatter for {item.name}: {e}")

                discovered.append(guideline_info)

    # Sort alphabetically by slug for consistent listing
    discovered.sort(key=lambda x: x['slug'])
    return discovered


# --- End Helper Functions ---
