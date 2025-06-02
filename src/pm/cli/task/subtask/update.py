# pm/cli/task/subtask/update.py
from typing import Optional
import click

from ....models import TaskStatus
from ....storage import update_subtask
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("update")
@click.argument("subtask_id")
@click.option("--name", help="New subtask name")
@click.option("--description", help="New subtask description")
@click.option("--required/--optional", default=None,  # Explicitly default to None
              help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="New subtask status")
@click.pass_context
def subtask_update(ctx, subtask_id: str, name: Optional[str], description: Optional[str],
                   required: Optional[bool], status: Optional[str]):
    """Update a subtask."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if required is not None:
            kwargs["required_for_completion"] = required
        if status is not None:
            kwargs["status"] = status

        subtask = update_subtask(conn, subtask_id, **kwargs)
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
