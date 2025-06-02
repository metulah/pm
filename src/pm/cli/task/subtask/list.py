# pm/cli/task/subtask/list.py
from typing import Optional
import click

from ....models import TaskStatus
from ....storage import list_subtasks
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("list")
@click.argument("task_id")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by subtask status")
@click.pass_context
def subtask_list(ctx, task_id: str, status: Optional[str]):
    """List subtasks for a task."""
    conn = get_db_connection()
    try:
        status_enum = TaskStatus(status) if status else None
        subtasks = list_subtasks(conn, task_id=task_id, status=status_enum)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", subtasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()
