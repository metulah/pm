# pm/cli/task/subtask/show.py
import click

from ....storage import get_subtask
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("show")
@click.argument("subtask_id")
@click.pass_context
def subtask_show(ctx, subtask_id: str):
    """Show subtask details."""
    conn = get_db_connection()
    try:
        subtask = get_subtask(conn, subtask_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if subtask:
            # Pass format and object
            click.echo(format_output(output_format, "success", subtask))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()
