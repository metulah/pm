# pm/core/guideline.py
import frontmatter
from pathlib import Path
from typing import List, Dict, Any

# Need to import RESOURCES_DIR and find_project_root
# Import from new core locations
from .constants import RESOURCES_DIR
from .utils import find_project_root


def get_available_guidelines() -> List[Dict[str, Any]]:
    """
    Discovers available guidelines, checking both built-in and custom.

    Scans the built-in resources directory and the project-specific
    '.pm/guidelines' directory (relative to project root). Custom guidelines
    override built-in ones with the same name (slug).

    Returns:
        A list of dictionaries, each representing a guideline:
        {'slug': str, 'description': str, 'type': str ('Built-in' or 'Custom'), 'path': Path}
        Returns an empty list if no guidelines are found or on error.
        The list is sorted alphabetically by slug.
    """
    guidelines_found: List[Dict[str, Any]] = []
    project_root_str = find_project_root()  # Find the project root dynamically
    # Convert to Path object if found
    project_root = Path(project_root_str) if project_root_str else None

    # --- Scan Built-in Guidelines ---
    if RESOURCES_DIR.is_dir():
        for item in RESOURCES_DIR.glob('welcome_guidelines_*.md'):
            if item.is_file():
                try:
                    slug = item.name.replace(
                        'welcome_guidelines_', '').replace('.md', '')
                    post = frontmatter.load(item)
                    # Use the more robust metadata handling from the custom section
                    actual_metadata = post.metadata.get('metadata', post.metadata) if isinstance(
                        post.metadata, dict) else post.metadata
                    description = actual_metadata.get('description', 'No description available.') if isinstance(
                        actual_metadata, dict) else 'No description available.'
                    title = actual_metadata.get('title', slug.replace('_', ' ').title()) if isinstance(
                        actual_metadata, dict) else slug.replace('_', ' ').title()
                    guidelines_found.append({
                        'slug': slug,
                        'title': title,
                        'description': description,
                        'type': 'Built-in',
                        'path': item
                    })
                except Exception as e:
                    # TODO: Replace print with proper logging/warning mechanism
                    print(
                        f"[Warning] Could not parse metadata from built-in {item.name}: {e}")
    else:
        # TODO: Replace print with proper logging/warning mechanism
        print(
            f"[Warning] Built-in resources directory not found: {RESOURCES_DIR}")

    # --- Scan Custom Guidelines ---
    # Check project_root Path object
    if project_root and project_root.is_dir():  # Ensure it's a directory too
        custom_dir = project_root / ".pm" / "guidelines"
        if custom_dir.is_dir():
            for item in custom_dir.glob('*.md'):
                if item.is_file():
                    try:
                        # Use stem for custom files (filename without ext)
                        slug = item.stem
                        post = frontmatter.load(item)

                        # Handle potential metadata nesting (as seen in list.py)
                        actual_metadata = post.metadata.get('metadata', post.metadata) if isinstance(
                            post.metadata, dict) else post.metadata
                        description = actual_metadata.get('description', 'No description available.') if isinstance(
                            actual_metadata, dict) else 'No description available.'
                        title = actual_metadata.get('title', slug.replace('_', ' ').title()) if isinstance(
                            actual_metadata, dict) else slug.replace('_', ' ').title()

                        # Check if a custom guideline with this slug already exists (shouldn't happen with glob)
                        # More importantly, check if it overrides a built-in one
                        existing_builtin_index = -1
                        for i, g in enumerate(guidelines_found):
                            if g['slug'] == slug and g['type'] == 'Built-in':
                                existing_builtin_index = i
                                break

                        custom_guideline_data = {
                            'slug': slug,
                            'title': title,
                            'description': description,
                            'type': 'Custom',
                            'path': item
                        }

                        if existing_builtin_index != -1:
                            # Override: Replace the built-in entry
                            guidelines_found[existing_builtin_index] = custom_guideline_data
                        else:
                            # Add new custom guideline if no built-in was overridden
                            # (Also handles cases where built-in didn't exist)
                            # Avoid adding duplicates if somehow scanned twice
                            if not any(g['slug'] == slug and g['type'] == 'Custom' for g in guidelines_found):
                                guidelines_found.append(custom_guideline_data)

                    except Exception as e:
                        # TODO: Replace print with proper logging/warning mechanism
                        print(
                            f"[Warning] Could not parse metadata from custom {item.name}: {e}")
        # else: Custom directory doesn't exist, which is fine.

    # Sort alphabetically by slug for consistent listing
    guidelines_found.sort(key=lambda x: x['slug'])

    return guidelines_found

# Ensure pm/core/__init__.py exists and potentially imports symbols if needed
