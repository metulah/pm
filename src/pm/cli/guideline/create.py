# pm/cli/guideline/create.py
import click
from . import utils  # Import helper functions from utils.py


@click.command()
@click.argument('name')
@click.option('--description', default=None, help='Description for the guideline (frontmatter).')
@click.option('--content', required=True, help='Content for the guideline, or use @<path> to load from file.')
@click.pass_context
def create_guideline(ctx, name, description, content):
    """Creates a new custom guideline in .pm/guidelines/."""
    custom_dir = utils._ensure_custom_dir()  # Use helper
    dest_path = custom_dir / f"{name}.md"

    if dest_path.exists():
        click.echo(
            f"Error: Custom guideline '{name}' already exists at {dest_path}", err=True)
        ctx.exit(1)

    try:
        guideline_content = utils._read_content_input(content)  # Use helper
        if guideline_content is None:
            # Should be caught by required=True, but good practice
            click.echo("Error: Content cannot be empty.", err=True)
            ctx.exit(1)

        metadata = {}
        if description:
            metadata['description'] = description

        utils._write_guideline(
            dest_path, guideline_content, metadata)  # Use helper
        click.echo(
            f"Successfully created custom guideline '{name}' at {dest_path}")

    except FileNotFoundError as e:
        click.echo(f"Error reading content file: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Error creating guideline '{name}': {e}", err=True)
        ctx.exit(1)
