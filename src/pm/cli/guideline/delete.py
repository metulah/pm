# pm/cli/guideline/delete.py
import click
from . import utils  # Import helper functions from utils.py


@click.command()
@click.argument('name')
@click.option('--force', is_flag=True, help='Required to confirm deletion.')
@click.pass_context
def delete_guideline(ctx, name, force):
    """Deletes a custom guideline from .pm/guidelines/."""
    guideline_path, guideline_type = utils._resolve_guideline_path(
        name)  # Use helper

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
