# pm/cli/project/tasks.py
from typing import Optional
import click

from ...models import TaskStatus
from ..common_utils import get_db_connection, format_output, resolve_project_identifier
from ..task.list import task_list  # Import task_list from its new location


@click.command("tasks")  # Add the click command decorator
@click.argument("identifier")  # Project identifier (ID or slug)
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by task status")
@click.option('--id', 'show_id', is_flag=True, default=False, help='Show the full ID column in text format.')
@click.option('--completed', 'include_completed', is_flag=True, default=False, help='Include completed tasks in the list (unless --status is used).')
@click.option('--description', 'show_description', is_flag=True, default=False, help='Show the full description column in text format.')
@click.option('--inactive', 'include_inactive_project_tasks', is_flag=True, default=False, help='Include tasks from non-ACTIVE projects.')
@click.pass_context
def project_tasks(ctx, identifier: str, status: Optional[str], show_id: bool, include_completed: bool, show_description: bool, include_inactive_project_tasks: bool):
    """List tasks for a specific project."""
    conn = None  # Initialize conn to None
    try:
        conn = get_db_connection()
        # Step 1: Resolve project identifier FIRST.
        # This raises click.UsageError if not found, which Click handles by exiting non-zero.
        # This line validates the project
        resolve_project_identifier(conn, identifier)

        # Step 2: If resolution succeeded, invoke task_list.
        # task_list handles its own errors internally for other issues.
        ctx.invoke(task_list, project=identifier, status=status, show_id=show_id,
                   include_completed=include_completed, show_description=show_description,
                   include_inactive_project_tasks=include_inactive_project_tasks)

    except click.ClickException:
        # Let Click handle its own exceptions (like UsageError from resolver)
        raise  # Re-raise for Click to handle
    except Exception as e:
        # Handle potential unexpected errors *during* task_list invocation
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=f"Unexpected error listing tasks for project '{identifier}': {e}"))
        ctx.exit(1)  # Ensure exit with non-zero code
    finally:
        # Ensure connection is closed even if resolver fails or invoke fails
        if conn:
            conn.close()
