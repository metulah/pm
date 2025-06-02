# pm/cli/task/delete.py
import click

from ...storage import delete_task
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier


@click.command("delete")  # Add the click command decorator
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.option('--force', is_flag=True, default=False, help='REQUIRED: Confirm irreversible deletion of task and associated data.')
@click.pass_context
def task_delete(ctx, project_identifier: str, task_identifier: str, force: bool):
    """Delete a task."""
    conn = get_db_connection()
    try:
        # Resolve project and task first to get the task ID
        project_obj = resolve_project_identifier(conn, project_identifier)
        task_to_delete = resolve_task_identifier(
            conn, project_obj, task_identifier)
        task_id = task_to_delete.id

        # Check for --force flag before proceeding
        if not force:
            raise click.UsageError(
                "Deleting a task is irreversible and will remove all associated subtasks, notes, etc. "
                "Use the --force flag to confirm."
            )

        success = delete_task(conn, task_id)  # Call delete with resolved ID
        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if not found, delete_task returns bool
        if success:
            click.echo(format_output(output_format, "success",
                       message=f"Task '{task_identifier}' deleted from project '{project_identifier}'"))
        else:
            # Should not be reached if resolver works
            click.echo(format_output(output_format, "error",
                       message=f"Failed to delete task '{task_identifier}'"))
    except click.ClickException:
        # Let Click handle its own exceptions (like UsageError)
        raise
    except Exception as e:  # Catch other unexpected errors
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=f"An unexpected error occurred: {e}"))
    finally:
        conn.close()
