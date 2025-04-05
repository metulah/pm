# pm/cli/guideline.py
import click
import os
import shutil
import frontmatter
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
# Assuming RESOURCES_DIR is defined in base or accessible
from .constants import RESOURCES_DIR  # Import from the new constants file

# Note: Custom guidelines directory is determined dynamically within functions using Path.cwd()

# --- Helper Functions ---


def _ensure_custom_dir():
    """Ensures the custom guidelines directory exists based on CWD."""
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    custom_dir.mkdir(parents=True, exist_ok=True)


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

# --- End Helper Functions ---

# Define the guideline command group


@click.group()
@click.pass_context
def guideline(ctx):
    """Commands for managing and viewing guidelines."""
    ctx.ensure_object(dict)
    pass

# Define the list subcommand


@guideline.command('list')
def list_guidelines():
    """Lists available built-in and custom guidelines."""
    click.echo("Scanning for guidelines...")
    guidelines_found = []
    console = Console()
    custom_dir = Path.cwd() / ".pm" / "guidelines"  # Get custom dir path

    # Scan Built-in Guidelines
    try:
        for item in RESOURCES_DIR.glob('welcome_guidelines_*.md'):
            if item.is_file():
                try:
                    name_part = item.name.replace(
                        'welcome_guidelines_', '').replace('.md', '')
                    post = frontmatter.load(item)
                    description = post.metadata.get(
                        'description', 'No description available.')
                    guidelines_found.append(
                        {'name': name_part, 'description': description, 'type': 'Built-in'})
                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Could not parse metadata from built-in {item.name}: {e}")

    except Exception as e:
        console.print(f"[red]Error scanning built-in guidelines: {e}[/red]")

    # Scan Custom Guidelines
    try:
        _ensure_custom_dir()
        for item in custom_dir.glob('*.md'):
            if item.is_file():
                try:
                    name_part = item.stem
                    post = frontmatter.load(item)
                    # Handle potential nesting when reading description
                    actual_metadata = post.metadata.get('metadata', post.metadata) if isinstance(
                        post.metadata, dict) else post.metadata
                    description = actual_metadata.get('description', 'No description available.') if isinstance(
                        actual_metadata, dict) else 'No description available.'

                    existing_custom_index = -1
                    for i, g in enumerate(guidelines_found):
                        if g['name'] == name_part and g['type'] == 'Custom':
                            existing_custom_index = i
                            break

                    if existing_custom_index == -1:
                        guidelines_found = [g for g in guidelines_found if not (
                            g['name'] == name_part and g['type'] == 'Built-in')]
                        guidelines_found.append(
                            {'name': name_part, 'description': description, 'type': 'Custom'})

                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Could not parse metadata from custom {item.name}: {e}")

    except Exception as e:
        console.print(f"[red]Error scanning custom guidelines: {e}[/red]")

    if not guidelines_found:
        click.echo("No guidelines found.")
        return

    guidelines_found.sort(key=lambda x: x['name'])

    click.echo("\nAvailable Guidelines:")
    for g in guidelines_found:
        click.echo(f"- {g['name']} [{g['type']}]: {g['description']}")
# Define the show subcommand


@guideline.command('show')
@click.argument('name')
@click.pass_context
def show_guideline(ctx, name):
    """Shows the content of a specific guideline (custom or built-in)."""
    console = Console()
    try:
        guideline_path, guideline_type = _resolve_guideline_path(name)

        if not guideline_path:
            click.echo(f"Error: Guideline '{name}' not found.", err=True)
            ctx.exit(1)

        click.echo(f"--- Displaying {guideline_type} Guideline: {name} ---")
        post = frontmatter.load(guideline_path)
        content = post.content

        markdown = Markdown(content)
        console.print(markdown)
        click.echo(f"--- End of Guideline: {name} ---")

    except Exception as e:
        click.echo(f"Error showing guideline '{name}': {e}", err=True)
        ctx.exit(1)


# --- New CRUD Commands ---

@guideline.command('create')
@click.argument('name')
@click.option('--description', default=None, help='Description for the guideline (frontmatter).')
@click.option('--content', required=True, help='Content for the guideline, or use @<path> to load from file.')
@click.pass_context
def create_guideline(ctx, name, description, content):
    """Creates a new custom guideline in .pm/guidelines/."""
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    _ensure_custom_dir()
    dest_path = custom_dir / f"{name}.md"

    if dest_path.exists():
        click.echo(
            f"Error: Custom guideline '{name}' already exists at {dest_path}", err=True)
        ctx.exit(1)

    try:
        guideline_content = _read_content_input(content)
        if guideline_content is None:
            click.echo(f"Error: Content cannot be empty.", err=True)
            ctx.exit(1)

        metadata = {}
        if description:
            metadata['description'] = description

        _write_guideline(dest_path, guideline_content, metadata)
        click.echo(
            f"Successfully created custom guideline '{name}' at {dest_path}")

    except FileNotFoundError as e:
        click.echo(f"Error reading content file: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Error creating guideline '{name}': {e}", err=True)
        ctx.exit(1)


@guideline.command('update')
@click.argument('name')
@click.option('--description', default=None, help='New description (replaces existing). Use "" to clear.')
@click.option('--content', default=None, help='New content, or use @<path>. Replaces existing content.')
@click.pass_context
def update_guideline(ctx, name, description, content):
    """Updates an existing custom guideline in .pm/guidelines/."""
    guideline_path, guideline_type = _resolve_guideline_path(name)

    if not guideline_path or guideline_type != "Custom":
        click.echo(f"Error: Custom guideline '{name}' not found.", err=True)
        ctx.exit(1)

    try:
        post = frontmatter.load(guideline_path)
        # Handle potential nesting when reading metadata
        current_metadata = post.metadata.get('metadata', post.metadata) if isinstance(
            post.metadata, dict) else (post.metadata or {})
        current_content = post.content

        if description is not None:
            if description == "":
                current_metadata.pop('description', None)
            else:
                current_metadata['description'] = description

        new_content = _read_content_input(content)
        final_content = new_content if new_content is not None else current_content

        _write_guideline(guideline_path, final_content, current_metadata)
        click.echo(f"Successfully updated custom guideline '{name}'.")

    except FileNotFoundError as e:
        click.echo(f"Error reading content file: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Error updating guideline '{name}': {e}", err=True)
        ctx.exit(1)


@guideline.command('delete')
@click.argument('name')
@click.option('--force', is_flag=True, help='Required to confirm deletion.')
@click.pass_context
def delete_guideline(ctx, name, force):
    """Deletes a custom guideline from .pm/guidelines/."""
    guideline_path, guideline_type = _resolve_guideline_path(name)

    if not guideline_path or guideline_type != "Custom":
        click.echo(f"Error: Custom guideline '{name}' not found.", err=True)
        ctx.exit(1)

    if not force:
        click.echo(
            f"Error: Deleting '{name}' requires the --force flag.", err=True)
        ctx.exit(1)

    try:
        guideline_path.unlink()
        click.echo(f"Successfully deleted custom guideline '{name}'.")
    except Exception as e:
        click.echo(f"Error deleting guideline '{name}': {e}", err=True)
        ctx.exit(1)


@guideline.command('copy')
@click.argument('source_name')
@click.argument('new_name')
@click.pass_context
def copy_guideline(ctx, source_name, new_name):
    """Copies a guideline (custom or built-in) to a new custom guideline."""
    custom_dir = Path.cwd() / ".pm" / "guidelines"
    _ensure_custom_dir()
    source_path, source_type = _resolve_guideline_path(source_name)
    dest_path = custom_dir / f"{new_name}.md"

    if not source_path:
        click.echo(
            f"Error: Source guideline '{source_name}' not found.", err=True)
        ctx.exit(1)

    if dest_path.exists():
        click.echo(
            f"Error: Destination custom guideline '{new_name}' already exists.", err=True)
        ctx.exit(1)

    try:
        post = frontmatter.load(source_path)
        # Extract the actual metadata, handling the nesting from load()
        actual_source_metadata = post.metadata.get('metadata', post.metadata) if isinstance(
            post.metadata, dict) else (post.metadata or {})
        _write_guideline(dest_path, post.content, actual_source_metadata)
        click.echo(
            f"Successfully copied '{source_name}' ({source_type}) to custom guideline '{new_name}'.")

    except Exception as e:
        click.echo(
            f"Error copying guideline '{source_name}' to '{new_name}': {e}", err=True)
        ctx.exit(1)
