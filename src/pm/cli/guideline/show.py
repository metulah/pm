# pm/cli/guideline/show.py
import click
import frontmatter
# Removed rich imports
from . import utils  # Import helper functions from utils.py


@click.command()
@click.argument('name')
@click.pass_context
def show_guideline(ctx, name):
    """Shows the content of a specific guideline (custom or built-in)."""
    # Removed rich Console instantiation
    try:
        guideline_path, guideline_type = utils._resolve_guideline_path(name)

        if not guideline_path:
            click.echo(f"Error: Guideline '{name}' not found.", err=True)
            ctx.exit(1)

        click.echo(f"--- Displaying {guideline_type} Guideline: {name} ---")
        post = frontmatter.load(guideline_path)
        content = post.content

        # Print raw content instead of rendering Markdown
        click.echo(content)
        click.echo(f"--- End of Guideline: {name} ---")

    except Exception as e:
        click.echo(f"Error showing guideline '{name}': {e}", err=True)
        ctx.exit(1)
