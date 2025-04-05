# pm/cli/guideline/list.py
import click
import frontmatter
from pathlib import Path
from rich.console import Console
from . import utils  # Import helper functions from utils.py
# Import RESOURCES_DIR from parent constants
from ..constants import RESOURCES_DIR


@click.command()
def list_guidelines():
    """Lists available built-in and custom guidelines."""
    click.echo("Scanning for guidelines...")
    guidelines_found = []
    console = Console()
    custom_dir = utils._ensure_custom_dir()  # Use helper and get path

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
        # custom_dir already ensured and retrieved above
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
                        # Remove built-in if custom with same name exists
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
