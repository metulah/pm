# pm/cli/guideline/update.py
import click
import frontmatter
from . import utils  # Import helper functions from utils.py


@click.command()
@click.argument('name')
@click.option('--description', default=None, help='New description (replaces existing). Use "" to clear.')
@click.option('--content', default=None, help='New content, or use @<path>. Replaces existing content.')
@click.pass_context
def update_guideline(ctx, name, description, content):
    """Updates an existing custom guideline in .pm/guidelines/."""
    guideline_path, guideline_type = utils._resolve_guideline_path(
        name)  # Use helper

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

        new_content = utils._read_content_input(content)  # Use helper
        final_content = new_content if new_content is not None else current_content

        utils._write_guideline(guideline_path, final_content,
                               current_metadata)  # Use helper
        click.echo(f"Successfully updated custom guideline '{name}'.")

    except FileNotFoundError as e:
        click.echo(f"Error reading content file: {e}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Error updating guideline '{name}': {e}", err=True)
        ctx.exit(1)
