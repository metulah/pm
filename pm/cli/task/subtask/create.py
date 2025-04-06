# pm/cli/task/subtask/create.py
import uuid
from typing import Optional
import click

from ....models import Subtask, TaskStatus
from ....storage import create_subtask
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("create")
@click.argument("task_id")
@click.option("--name", required=True, help="Subtask name")
@click.option("--description", help="Subtask description")
@click.option("--required/--optional", default=True,
              help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              default=TaskStatus.NOT_STARTED.value, help="Subtask status")
@click.pass_context
def subtask_create(ctx, task_id: str, name: str, description: Optional[str],
                   required: bool, status: str):
    """Create a new subtask."""
    conn = get_db_connection()
    try:
        subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id=task_id,
            name=name,
            description=description,
            required_for_completion=required,
            status=TaskStatus(status)
        )
        subtask = create_subtask(conn, subtask)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", subtask))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()
