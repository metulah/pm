# pm/cli/guideline/copy.py
import click
import frontmatter
from . import utils  # Import helper functions from utils.py


@click.command()
@click.argument('source_name')
@click.argument('new_name')
@click.pass_context
def copy_guideline(ctx, source_name, new_name):
    """Copies a guideline (custom or built-in) to a new custom guideline."""
    custom_dir = utils._ensure_custom_dir()  # Use helper
    source_path, source_type = utils._resolve_guideline_path(
        source_name)  # Use helper
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
        utils._write_guideline(dest_path, post.content,
                               actual_source_metadata)  # Use helper
        click.echo(
            f"Successfully copied '{source_name}' ({source_type}) to custom guideline '{new_name}'.")

    except Exception as e:
        click.echo(
            f"Error copying guideline '{source_name}' to '{new_name}': {e}", err=True)
        ctx.exit(1)
