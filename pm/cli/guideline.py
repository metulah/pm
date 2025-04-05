# pm/cli/guideline.py
import click
import os
import frontmatter
from pathlib import Path
# Assuming RESOURCES_DIR is defined in base or accessible
from .constants import RESOURCES_DIR  # Import from the new constants file

# Define the guideline command group


@click.group()
def guideline():
    """Commands for managing and viewing guidelines."""
    pass

# Define the list subcommand


@guideline.command('list')
def list_guidelines():
    """Lists available built-in guidelines and their descriptions."""
    click.echo("Scanning for guidelines...")
    guidelines_found = []
    try:
        for item in RESOURCES_DIR.glob('welcome_guidelines_*.md'):
            if item.is_file():
                try:
                    # Extract name (e.g., 'coding' from 'welcome_guidelines_coding.md')
                    name_part = item.name.replace(
                        'welcome_guidelines_', '').replace('.md', '')

                    # Parse front matter
                    post = frontmatter.load(item)
                    description = post.metadata.get(
                        'description', 'No description available.')

                    guidelines_found.append(
                        {'name': name_part, 'description': description})
                except Exception as e:
                    click.echo(
                        f"Warning: Could not parse metadata from {item.name}: {e}", err=True)
                    # Optionally still list the file but without description
                    # guidelines_found.append({'name': name_part, 'description': 'Error parsing metadata.'})

        if not guidelines_found:
            click.echo("No built-in guidelines found.")
            return

        # Sort alphabetically by name for consistent output
        guidelines_found.sort(key=lambda x: x['name'])

        # Print the list (simple format for now)
        click.echo("\nAvailable Guidelines:")
        for g in guidelines_found:
            click.echo(f"- {g['name']}: {g['description']}")

    except Exception as e:
        click.echo(f"Error scanning for guidelines: {e}", err=True)

# Add more subcommands to the 'guideline' group here later if needed
# e.g., @guideline.command('show') ...
