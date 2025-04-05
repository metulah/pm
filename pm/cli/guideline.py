# pm/cli/guideline.py
import click
import os
import frontmatter
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
# Assuming RESOURCES_DIR is defined in base or accessible
from .constants import RESOURCES_DIR  # Import from the new constants file

# Define the guideline command group


@click.group()
@click.pass_context
def guideline(ctx):
    """Commands for managing and viewing guidelines."""
    # ensure that ctx.obj exists and is a dict (in case `cli` is called
    # by means other than the `if __name__ == "__main__":` block below)
    ctx.ensure_object(dict)
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
# Define the show subcommand


@guideline.command('show')
@click.argument('name')
@click.pass_context
def show_guideline(ctx, name):
    """Shows the content of a specific guideline."""
    console = Console()
    try:
        # Construct the expected filename
        guideline_filename = f"welcome_guidelines_{name}.md"
        guideline_path = RESOURCES_DIR / guideline_filename

        if not guideline_path.is_file():
            click.echo(
                f"Error: Guideline '{name}' not found at expected location {guideline_path}", err=True)
            ctx.exit(1)
            return  # Redundant due to ctx.exit, but good practice

        # Read the full content of the file
        # Use frontmatter.load to handle potential metadata, but get the raw content
        post = frontmatter.load(guideline_path)
        content = post.content  # Get content after frontmatter

        # Render the Markdown content
        markdown = Markdown(content)
        console.print(markdown)

    except Exception as e:
        click.echo(f"Error showing guideline '{name}': {e}", err=True)
        ctx.exit(1)
