# pm/cli/task/subtask/delete.py
import click

from ....storage import delete_subtask
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("delete")
@click.argument("subtask_id")
@click.pass_context
def subtask_delete(ctx, subtask_id: str):
    """Delete a subtask."""
    conn = get_db_connection()
    try:
        success = delete_subtask(conn, subtask_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Subtask {subtask_id} deleted"))
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
